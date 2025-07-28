# backend/utils/io.py

import redis
import json
import pandas as pd

r = redis.Redis(decode_responses=True)

def read_sample_ids_for_entity(file_path: str) -> list[str]:
    try:
        sep = "\t" if file_path.endswith((".tsv", ".txt")) else ","
        df = pd.read_csv(file_path, sep=sep, usecols=[0])
        first_col = df.columns[0]
        return df[first_col].astype(str).tolist()
    except Exception as e:
        raise RuntimeError(f"Failed to read sample IDs from {file_path}: {e}")

def load_common_ids_from_redis(job_id: str) -> list[str]:
    redis_key = f"common_ids:{job_id}"
    value = r.get(redis_key)
    if value is None:
        raise ValueError(f"Common IDs not found for job {job_id}")
    return json.loads(value)

def find_entity_cfg_by_label(cfgs: list[dict], feature_label: str) -> dict:
    for cfg in cfgs:
        if cfg["feature_label"] == feature_label:
            return cfg
    raise ValueError(f"No entity found with feature_label '{feature_label}'")

def load_mappings_from_redis(job_id: str) -> list[dict]:
    redis_key = f"mappings:{job_id}"
    raw = r.get(redis_key)
    if not raw:
        raise ValueError(f"No soft match mappings found for job_id: {job_id}")

    try:
        mappings = json.loads(raw)
        if not isinstance(mappings, list):
            raise ValueError(f"Expected list but got {type(mappings)}")
        return mappings
    except json.JSONDecodeError:
        raise ValueError(f"Redis data for job_id {job_id} is not valid JSON")
    except Exception as e:
        raise ValueError(f"Unexpected error parsing mappings for job_id {job_id}: {e}")