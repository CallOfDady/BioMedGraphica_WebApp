# backend/tasks/steps.py

import os
import numpy as np
import pandas as pd
import json
import redis
import logging
from celery import group
from backend.celery_worker import celery_app
from backend.service.hard_match import process_entity_hard_match
from backend.service.soft_match import generate_soft_match_candidates, apply_soft_match_selection
from backend.service.finalize import finalize
from backend.service.task_tracker import update_task_status
from backend.utils.io import read_sample_ids_for_entity, load_common_ids_from_redis, find_entity_cfg_by_label, load_mappings_from_redis

r = redis.Redis()

@celery_app.task
def compute_common_id_task(entities_cfgs, job_id):
    print(f"[compute_common] job: {job_id}")
    
    sample_sets = []

    for cfg in entities_cfgs:
        if not cfg.get("fill0", False) and cfg["entity_type"].lower() != "label":
            sample_ids = read_sample_ids_for_entity(cfg["file_path"])
            sample_sets.append(set(sample_ids))

    if not sample_sets:
        raise ValueError("No valid input files found to compute sample ID intersection.")

    common_ids = sorted(list(set.intersection(*sample_sets)))

    r.set(f"common_ids:{job_id}", json.dumps(common_ids))

    print(f"Common sample IDs for job `{job_id}`: {len(common_ids)} found")
    return common_ids

@celery_app.task
def run_label_task(label_cfg, output_dir, job_id, common_ids=None):
    feature_label = label_cfg.get("feature_label")
    file_path = label_cfg.get("file_path")
    entity_type = label_cfg.get("entity_type", "").lower()
    label_type = label_cfg.get("label_type", "binary") # Default to binary if not specified

    print(f"[run_label] job: {job_id} - {feature_label}")

    # Step 1: Load common_ids if not passed
    if common_ids is None:
        common_ids = load_common_ids_from_redis(job_id)

    # Step 2: Validate entity type
    if label_type == "binary":
        if entity_type != "label":
            error = "Invalid entity_type for label"
            update_task_status(job_id, "failed", {"error": error})
            return {"feature_label": feature_label, "status": "error", "error": error}

        try:
            sep = "\t" if file_path.endswith((".tsv", ".txt")) else ","
            df = pd.read_csv(file_path, sep=sep)

            if df.shape[1] < 2:
                error = "Label file must contain at least two columns (sample ID + label)"
                update_task_status(job_id, "failed", {"error": error})
                return {"feature_label": feature_label, "status": "error", "error": error}

            df.rename(columns={df.columns[0]: "Sample_ID"}, inplace=True)
            df["Sample_ID"] = df["Sample_ID"].astype(str)
            df = df[df["Sample_ID"].isin(common_ids)]
            df.set_index("Sample_ID", inplace=True)
            label_col = df.columns[0]
            df = df[[label_col]].reindex(common_ids).fillna(0)

            labels = df[label_col].values

            # Save output
            label_temp_output_dir = os.path.join(output_dir, "_y")
            os.makedirs(label_temp_output_dir, exist_ok=True)
            np.save(os.path.join(label_temp_output_dir, f"{feature_label}.npy"), labels)

            return {"feature_label": feature_label, "status": "success"}

        except Exception as e:
            error = str(e)
            update_task_status(job_id, "failed", {"error": error})
            return {"feature_label": feature_label, "status": "error", "error": error}

    else:
        error = f"Unknown label_type: {label_type}"
        update_task_status(job_id, "failed", {"error": error})
        return {"feature_label": feature_label, "status": "error", "error": error}


@celery_app.task
def run_hard_match_task(ent_cfg, database_path, output_dir, job_id, common_ids):
    print(f"[run_hard] {ent_cfg['feature_label']} for job: {job_id}")
    
    try:
        result = process_entity_hard_match(
            entity_type=ent_cfg["entity_type"],
            id_type=ent_cfg["id_type"],
            file_path=ent_cfg["file_path"],
            feature_label=ent_cfg["feature_label"],
            database_path=database_path,
            fill0=ent_cfg.get("fill0", False),
            sample_ids=common_ids,
            output_dir=output_dir
        )

        print(f"[run_hard] Completed for {ent_cfg['feature_label']} with status: {result['status']}")
        return {
            "job_id": job_id,
            "feature_label": ent_cfg["feature_label"],
            "status": result["status"]
        }

    except Exception as e:
        logging.exception(f"❌ [run_hard] Failed for {ent_cfg['feature_label']}")
        return {
            "job_id": job_id,
            "feature_label": ent_cfg["feature_label"],
            "status": "error",
            "error": str(e)
        }

@celery_app.task
def run_soft_match_generate(ent_cfg, database_path, job_id):
    feature_label = ent_cfg["feature_label"]
    print(f"[run_soft:generate] {feature_label} for job: {job_id}")

    candidates = generate_soft_match_candidates(
        entity_type=ent_cfg["entity_type"],
        file_path=ent_cfg["file_path"],
        feature_label=feature_label,
        database_path=database_path,
        topk=5
    )

    redis_key = f"softmatch:{job_id}"
    existing = r.get(redis_key)
    all_candidates = json.loads(existing) if existing else []

    all_candidates.append({
        "feature_label": feature_label,
        "entity_type": ent_cfg["entity_type"],
        "candidates": candidates
    })

    r.set(redis_key, json.dumps(all_candidates))

    # Awaiting user mapping
    from backend.service.task_tracker import update_task_status
    update_task_status(ent_cfg["task_id"], "awaiting_mapping", {
        "mapping_candidates": all_candidates
    })

    # NOTE: This task does not return anything as it is awaiting user input
    return "awaiting_mapping"

@celery_app.task
def run_soft_match_apply(ent_cfg, database_path, output_dir, job_id, confirmed_mapping, common_ids):
    feature_label = ent_cfg["feature_label"]
    print(f"[run_soft:apply] {feature_label} for job: {job_id}")


    # 1. Apply mapping (confirmed_mapping is List[Dict[str, Any]])
    # 2. Load feature table + mapping ID + align common_ids
    # 3. Construct numpy/tensor data, etc.

    print("[DEBUG] Confirmed mapping:")
    print(confirmed_mapping)
    print(type(confirmed_mapping))

    # 1. Parse user mapping into dictionary: {original_id: selected_id or None}
    mappings_list = confirmed_mapping.get("mappings", [])
    user_selections = {
        m["original_id"]: m["selected_id"]
        for m in mappings_list if m.get("original_id") is not None
    }

    # 3. Run soft match processing
    result = apply_soft_match_selection(
        entity_type=ent_cfg["entity_type"],
        file_path=ent_cfg["file_path"],
        feature_label=feature_label,
        database_path=database_path,
        sample_ids=common_ids,
        user_selections=user_selections,
        output_dir=output_dir
    )

    print(f"[run_soft:apply] Finished for {feature_label} → Status: {result.get('status')}")
    return result

@celery_app.task
def finalize_task(finalize_cfg, database_path, output_dir, job_id):
    print(f"[finalize] job: {job_id}")
    
    try:
        file_order = finalize_cfg.get("file_order", [])
        apply_zscore = finalize_cfg.get("apply_zscore", False)
        edge_types = finalize_cfg.get("edge_types", None)

        if not file_order:
            raise ValueError("file_order is required for finalization")

        result = finalize(
            database_path=database_path,
            cache_dir=output_dir,
            file_order=file_order,
            edge_types=edge_types,
            apply_zscore=apply_zscore
        )

        print(f"Finalization complete for job {job_id}")
        return {
            "status": "success",
            "job_id": job_id,
            "result": result
        }

    except Exception as e:
        logging.exception(f"Finalization failed for job {job_id}")
        return {
            "status": "error",
            "job_id": job_id,
            "error": str(e)
        }
    
@celery_app.task
def launch_processing_task(common_ids, config):
    entities_cfgs = config["entities_cfgs"]
    label_cfg = config.get("label_cfg")
    job_id = config["job_id"]
    task_id = config["task_id"]
    output_dir = config["output_dir"]
    database_path = config["database_path"]

    mappings = load_mappings_from_redis(job_id)

    parallel_tasks = []

    if label_cfg:
        parallel_tasks.append(run_label_task.s(label_cfg, output_dir, job_id, common_ids))

    for ent in entities_cfgs:
        mode = ent.get("match_mode", "hard").lower()
        if mode == "hard":
            parallel_tasks.append(run_hard_match_task.s(ent, database_path, output_dir, job_id, common_ids))
        elif mode == "soft":
            mapping_item = next((m for m in mappings if m["feature_label"] == ent["feature_label"]), None)
            parallel_tasks.append(run_soft_match_apply.s(ent, database_path, output_dir, job_id, mapping_item, common_ids))

    update_task_status(task_id, "processing", {"message": "Main processing tasks running..."})
    return True

@celery_app.task
def finalize_stage_task(results, config):
    finalize_cfg = config["finalize"]
    database_path = config["database_path"]
    output_dir = config["output_dir"]
    job_id = config["job_id"]
    task_id = config["task_id"]

    # Common IDs will be passed from the previous step
    return finalize_task.s(finalize_cfg, database_path, output_dir, job_id)()