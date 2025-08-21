# backend/utils/io.py

import os
import time
import redis
import json
import pandas as pd
import torch

r = redis.Redis(decode_responses=True)

def read_sample_ids_for_entity(file_path: str, max_retries: int = 3, delay: float = 1) -> list[str]:
    sep = "\t" if file_path.endswith((".tsv", ".txt")) else ","
    
    for attempt in range(1, max_retries + 1):
        try:
            df = pd.read_csv(file_path, sep=sep, usecols=[0])
            first_col = df.columns[0]
            return df[first_col].astype(str).tolist()
        except Exception as e:
            print(f"[Retry {attempt}/{max_retries}] Failed to read `{file_path}`: {e}")
            if attempt == max_retries:
                raise RuntimeError(f"Failed to read sample IDs from {file_path} after {max_retries} attempts: {e}")
            time.sleep(delay)  # Wait before retrying


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
        # Return empty list if no mappings found (for hard match only scenarios)
        return []

    try:
        mappings = json.loads(raw)
        if not isinstance(mappings, list):
            raise ValueError(f"Expected list but got {type(mappings)}")
        return mappings
    except json.JSONDecodeError:
        raise ValueError(f"Redis data for job_id {job_id} is not valid JSON")
    except Exception as e:
        raise ValueError(f"Unexpected error parsing mappings for job_id {job_id}: {e}")

def _load_bmg_csv(database_path, entity_type):
    path = os.path.join(
        database_path,
        "Entity",
        entity_type,
        f"BioMedGraphica_Conn_{entity_type}.csv",
    )
    if not os.path.exists(path):
        raise FileNotFoundError(f"Mapping file not found: {path}")
    return pd.read_csv(path)

def _load_bmg_embeddings(database_path, entity_type):
    path = os.path.join(
        database_path,
        "Embed",
        entity_type,
        f"{entity_type}_Embeddings.pt",
    )
    if not os.path.exists(path):
        raise FileNotFoundError(f"Embedding file not found: {path}")
    return torch.load(path, map_location=torch.device('cpu'))

def _load_bmg_name_csv(database_path, entity_type):
    path = os.path.join(
        database_path,
        "Entity",
        entity_type,
        f"BioMedGraphica_Conn_{entity_type}_LLM_Name_ID_Combined.csv",
    )
    if not os.path.exists(path):
        raise FileNotFoundError(f"Mapping file not found: {path}")
    return pd.read_csv(path)

def _load_bmg_desc_csv(database_path, entity_type):
    path = os.path.join(
        database_path,
        "Entity",
        entity_type,
        f"BioMedGraphica_Conn_{entity_type}_Description_Combined.csv",
    )
    if not os.path.exists(path):
        raise FileNotFoundError(f"Mapping file not found: {path}")
    return pd.read_csv(path)

def save_name_and_desc(database_path, entity_type, output_dir, feature_label):
    # Save entity name if available
    try:
        name_df = _load_bmg_name_csv(database_path, entity_type)
        if "BioMedGraphica_Conn_ID" in name_df.columns and "Names_and_IDs" in name_df.columns:
            name_df = name_df[["BioMedGraphica_Conn_ID", "Names_and_IDs"]]
            name_df.to_csv(
                os.path.join(output_dir, "_x", f"{feature_label.lower()}_name.csv"),
                index=False
            )
    except FileNotFoundError as e:
        print(f"[WARN] {entity_type} Name file not found: {e}")

    # Save entity description if available
    try:
        desc_df = _load_bmg_desc_csv(database_path, entity_type)
        if "BioMedGraphica_Conn_ID" in desc_df.columns and "Description" in desc_df.columns:
            desc_df = desc_df[["BioMedGraphica_Conn_ID", "Description"]]
            desc_df.to_csv(
                os.path.join(output_dir, "_x", f"{feature_label.lower()}_desc.csv"),
                index=False
            )
    except FileNotFoundError as e:
        print(f"[WARN] {entity_type} Description file not found: {e}")