# backend/service/task_submitter.py

from typing import List, Optional
from backend.service.task_tracker import store_task_status
from backend.api.schemas import EntityConfig, LabelConfig, FinalConfig
from backend.tasks.pipeline import submit_processing_task  # Celery task entry point

def submit_job_to_pipeline(
    job_id: str,
    entities_cfgs: List[EntityConfig],
    label_cfg: Optional[LabelConfig],
    finalize: FinalConfig,
    database_path: str,
    output_dir: str,
    task_id: Optional[str] = None  # new: support resume
) -> str:
    """
    Submit full processing pipeline to Celery via submit_processing_task().
    Supports both fresh submissions and resume-from-mapping.
    """
    if not task_id:
        from uuid import uuid4
        task_id = str(uuid4())

    config_payload = {
        "task_id": task_id,
        "job_id": job_id,
        "entities_cfgs": [e.model_dump() for e in entities_cfgs],
        "label_cfg": label_cfg.model_dump() if label_cfg else None,
        "finalize": finalize.model_dump(),
        "database_path": database_path,
        "output_dir": output_dir
    }

    # Submit to Celery
    import json

    try:
        json.dumps(config_payload)
    except TypeError as e:
        print("Serialization error:", e)
    submit_processing_task.delay(config_payload)

    # Store status (only if not already submitted earlier)
    store_task_status(task_id, {
        "job_id": job_id,
        "status": "submitted",
        "progress": 0,
        "message": "Task submitted to processing pipeline."
    })

    return task_id
