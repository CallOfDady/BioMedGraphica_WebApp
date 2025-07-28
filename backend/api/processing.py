# backend/api/processing.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from backend.api.schemas import EntityConfig, LabelConfig, FinalConfig
from backend.service.task_submitter import submit_job_to_pipeline
from backend.service.task_tracker import update_task_status, get_task_status
from backend.service.soft_match import generate_soft_match_candidates
from backend.tasks.steps import run_soft_match_apply
from backend.utils.io import load_common_ids_from_redis, find_entity_cfg_by_label
import logging
import redis
import json
import uuid


r = redis.Redis()

router = APIRouter()

# ---------------------------
# Request/Response Schemas
# ---------------------------

# class EntityConfig(BaseModel):
#     feature_label: str
#     entity_type: str
#     id_type: Optional[str]
#     match_mode: str
#     file_path: str
#     fill0: bool = False

# class LabelConfig(BaseModel):
#     feature_label: str
#     entity_type: str
#     id_type: Optional[str]
#     file_path: str
#     fill0: bool = False

# class FinalConfig(BaseModel):
#     file_order: Optional[List[str]]
#     apply_zscore: bool = False
#     edge_types: Optional[List[str]]

# Mapping models for soft match
class MappingItem(BaseModel):
    original_id: str
    selected_id: Optional[str]
    selected_label: Optional[str]

class FeatureMapping(BaseModel):
    entity_type: str
    feature_label: str
    mappings: List[MappingItem]

class MappingSubmission(BaseModel):
    task_id: str
    mappings: List[FeatureMapping]


class ProcessingRequest(BaseModel):
    job_id: str
    entities_cfgs: List[EntityConfig]
    label_cfg: Optional[LabelConfig]
    finalize: FinalConfig
    database_path: str
    output_dir: str

class ProcessingResponse(BaseModel):
    task_id: str
    status: str = "submitted"
    message: Optional[str] = None

# ---------------------------
# API Endpoints
# ---------------------------

@router.post("/submit", response_model=ProcessingResponse)
def submit_processing(req: ProcessingRequest, background_tasks: BackgroundTasks):
    """
    Submit a processing task. If soft match is required, delay execution until mappings are confirmed.
    """
    try:
        task_id = str(uuid.uuid4())
        job_id = req.job_id

        # Check for soft match
        soft_cfgs = [e.model_dump() for e in req.entities_cfgs if e.match_mode == "soft"]
        print(f"[DEBUG] Soft match configurations: {soft_cfgs}")

        if soft_cfgs:
            all_candidates = []
            for cfg in soft_cfgs:
                topk_result = generate_soft_match_candidates(
                    entity_type=cfg["entity_type"],
                    file_path=cfg["file_path"],
                    feature_label=cfg["feature_label"],
                    database_path=req.database_path,
                    topk=5
                )

                all_candidates.append(topk_result)

            r.set(f"softmatch:{job_id}", json.dumps(all_candidates))

            update_task_status(task_id, "awaiting_mapping", {
                "job_id": job_id,
                "entities_cfgs": [e.model_dump() for e in req.entities_cfgs],
                "label_cfg": req.label_cfg.model_dump() if req.label_cfg else None,
                "finalize": req.finalize.model_dump(),
                "database_path": req.database_path,
                "output_dir": req.output_dir
            })

            return ProcessingResponse(task_id=task_id, status="awaiting_mapping", message="Awaiting user mapping selection.")

        # No soft match, proceed directly
        pipeline_task_id = submit_job_to_pipeline(
            task_id=task_id,
            job_id=req.job_id,
            entities_cfgs=req.entities_cfgs,
            label_cfg=req.label_cfg,
            finalize=req.finalize,
            database_path=req.database_path,
            output_dir=req.output_dir
        )

        return ProcessingResponse(task_id=pipeline_task_id)

    except Exception as e:
        logging.exception("Failed to submit processing task")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submit-mappings")
def submit_mappings(data: MappingSubmission):
    task_id = data.task_id
    mappings = data.mappings

    task_info = get_task_status(task_id)
    if not task_info or task_info["status"] != "awaiting_mapping":
        raise HTTPException(status_code=400, detail="Invalid mapping state")

    job_id = task_info["job_id"]

    # Store mappings in Redis for downstream access
    redis_mapping_key = f"mappings:{job_id}"
    r.set(redis_mapping_key, json.dumps([m.model_dump() for m in mappings]))

    # Resume pipeline
    pipeline_task_id = submit_job_to_pipeline(
        task_id=task_id,
        job_id=job_id,
        entities_cfgs=[EntityConfig(**e) for e in task_info["entities_cfgs"]],
        label_cfg=LabelConfig(**task_info["label_cfg"]) if task_info.get("label_cfg") else None,
        finalize=FinalConfig(**task_info["finalize"]),
        database_path=task_info["database_path"],
        output_dir=task_info["output_dir"]
    )

    update_task_status(task_id, "resuming", {"message": "Soft match mappings submitted. Resuming processing."})
    return {"message": "Mappings received and processing resumed."}

@router.get("/status/{task_id}")
def check_task_status(task_id: str):
    try:
        status_info = get_task_status(task_id)

        # If task is awaiting mapping, fetch candidates from Redis
        if status_info and status_info.get("status") == "awaiting_mapping":
            job_id = status_info.get("job_id") or status_info.get("metadata", {}).get("job_id")
            if job_id:
                redis_key = f"softmatch:{job_id}"
                raw_candidates = r.get(redis_key)
                if raw_candidates:
                    mapping_candidates = json.loads(raw_candidates)
                    status_info["mapping_candidates"] = mapping_candidates

        return status_info
    except Exception as e:
        logging.exception(f"Failed to get status for task {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")