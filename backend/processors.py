import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from backend.finalize import finalize
from backend.hard_match import process_entity_hard_match
from backend.soft_match import process_entity_soft_match

__all__ = ["process"]


def _read_sample_ids(file_path):
    sep = "\t" if file_path.endswith((".tsv", ".txt")) else ","
    df = pd.read_csv(file_path, sep=sep, usecols=[0])
    first_col = df.columns[0]
    return df[first_col].astype(str).tolist()

def _compute_common_sample_ids(configs):
    sample_sets = []
    for cfg in configs:
        if not cfg.get("fill0", False) and cfg["entity_type"].lower() != "label":
            sample_ids = _read_sample_ids(cfg["file_path"])
            sample_sets.append(set(sample_ids))
    if not sample_sets:
        raise ValueError("At least one entity must supply data to derive sample IDs")
    
    common_ids = set.intersection(*sample_sets)
    return sorted([str(sid) for sid in common_ids])

def _process_label(cfg, common_ids, output_dir):
    feature_label = cfg.get("feature_label")
    file_path = cfg.get("file_path")
    entity_type = cfg.get("entity_type", "").lower()
    label_type = cfg.get("label_type", "binary")

    if label_type == "binary":
        if entity_type != "label":
            return {"feature_label": feature_label, "status": "error", "error": "Invalid entity_type for label"}

        try:
            sep = "\t" if file_path.endswith((".tsv", ".txt")) else ","
            df = pd.read_csv(file_path, sep=sep)
            if df.shape[1] < 2:
                return {
                    "feature_label": feature_label,
                    "status": "error",
                    "error": "Label file must contain at least two columns (sample ID + label)"
                }

            df.rename(columns={df.columns[0]: "Sample_ID"}, inplace=True)
            df["Sample_ID"] = df["Sample_ID"].astype(str)
            df = df[df["Sample_ID"].isin(common_ids)]
            df.set_index("Sample_ID", inplace=True)
            label_col = df.columns[0]
            df = df[[label_col]].reindex(common_ids).fillna(0)
            labels = df[label_col].values

            y_dir = os.path.join(output_dir, "_y")
            os.makedirs(y_dir, exist_ok=True)

            np.save(os.path.join(y_dir, f"{feature_label}.npy"), labels)
            # df.to_csv(os.path.join(y_dir, f"{feature_label}.csv"))

            return {"feature_label": feature_label, "status": "success"}
        except Exception as e:
            return {"feature_label": feature_label, "status": "error", "error": str(e)}
    else:
        return {"feature_label": feature_label, "status": "error", "error": f"Unknown label_type: {label_type}"}


def _process_omics_entity(cfg, common_ids, database_path, output_dir):
    feature_label = cfg["feature_label"]
    entity_type = cfg["entity_type"]
    id_type = cfg.get("id_type", "")
    file_path = cfg.get("file_path", "")
    fill0 = cfg.get("fill0", False)
    match_mode = cfg.get("match_mode", "hard").lower()
    
    # Debug: Print the configuration for all entities
    print(f" Entity configuration:")
    print(f" - feature_label: {feature_label}")
    print(f" - entity_type: {entity_type}")
    print(f" - id_type: {id_type}")
    print(f" - match_mode: {match_mode}")
    print(f" - file_path: {file_path}")
    print(f" - fill0: {fill0}")

    if (fill0) and id_type:
        print(f"Error: fill0={fill0} and id_type='{id_type}' for {entity_type}")
        return {"feature_label": feature_label, "status": "error", "error": "id_type must be empty for fill0"}

    try:
        # Validate match_mode
        if match_mode not in ("hard", "soft"):
            return {
                "feature_label": feature_label,
                "status": "error",
                "error": f"Unknown match_mode '{match_mode}', expected 'hard' or 'soft'"
            }

        # Handle virtual nodes with soft mode
        if fill0 and match_mode == "soft":
            print(f"Warning: Virtual node {feature_label} has soft match mode - switching to hard")
            match_mode = "hard"

        # If not a virtual node, check file existence
        if not fill0 and not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return {
                "feature_label": feature_label,
                "status": "error",
                "error": f"File not found: {file_path}"
            }

        if match_mode == "hard":
            print(f"Processing (hard match): {feature_label}")
            return process_entity_hard_match(
                entity_type=entity_type,
                id_type=id_type,
                file_path=file_path,
                feature_label=feature_label,
                database_path=database_path,
                fill0=fill0,
                sample_ids=common_ids,
                output_dir=output_dir,
            )

        elif match_mode == "soft":
            print(f"Processing (soft match): {feature_label}")
            return process_entity_soft_match(
                entity_type=entity_type,
                file_path=file_path,
                feature_label=feature_label,
                database_path=database_path,
                sample_ids=common_ids,
                output_dir=output_dir,
                interactive_mode=True,
            )

    except Exception as e:
        return {
            "feature_label": feature_label,
            "status": "error",
            "error": str(e)
        }

def process(*configs, database_path, output_dir, file_order=None, apply_zscore=False, edge_types=None):
    common_ids = _compute_common_sample_ids(configs)
    results = []

    # Step 1: process labels
    for cfg in [c for c in configs if c["entity_type"].lower() == "label"]:
        results.append(_process_label(cfg, common_ids, output_dir))

    # Step 2: process omics entities
    omics_cfgs = [c for c in configs if c["entity_type"].lower() != "label"]
    
    # Sort configurations to prioritize soft match entities first
    soft_match_cfgs = [cfg for cfg in omics_cfgs if cfg.get("match_mode", "hard").lower() == "soft"]
    hard_match_cfgs = [cfg for cfg in omics_cfgs if cfg.get("match_mode", "hard").lower() == "hard"]
    
    # Process soft match entities first, then hard match entities
    ordered_cfgs = soft_match_cfgs + hard_match_cfgs
    
    print(f"Found {len(omics_cfgs)} omics entities to process:")
    print(f"  - {len(soft_match_cfgs)} soft match entities (processed first)")
    print(f"  - {len(hard_match_cfgs)} hard match entities (processed after)")
    
    for i, cfg in enumerate(ordered_cfgs):
        priority = "SOFT" if cfg.get("match_mode", "hard").lower() == "soft" else "🔧 HARD"
        print(f" {i+1}. {cfg['feature_label']} ({cfg['entity_type']}) - {priority}")
    
    for cfg in tqdm(ordered_cfgs, desc="Processing", unit="entity"):
        print(f"\nProcessing entity: {cfg['feature_label']}")
        result = _process_omics_entity(cfg, common_ids, database_path, output_dir)
        print(f"  Result: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'error':
            print(f"  Error: {result.get('error', 'unknown error')}")
        elif result.get('status') == 'pending_user_selection':
            print(f"  Waiting for user selection: {result.get('message', 'Please complete mappings')}")
            # Store this pending result and continue the loop (don't return immediately)
            results.append(result)
            
            # After each entity that needs mapping, return to the UI to let user complete mappings
            return {
                "common_sample_ids": common_ids,
                "results": results,  # Include all results so far
                "summary": {
                    "total": len(results),
                    "success": sum(1 for r in results if r["status"] == "success"),
                    "error": sum(1 for r in results if r["status"] == "error"),
                    "pending": sum(1 for r in results if r["status"] == "pending_user_selection")
                },
                "status": "pending_user_interaction",
                "message": f"Please complete ID mappings for {cfg['feature_label']} and rerun the process."
            }
        
        results.append(result)

    # Step 3: prepare feature_order
    # Use original omics_cfgs order for feature_order, not the processing order
    available_labels = [cfg["feature_label"] for cfg in omics_cfgs]
    if file_order is None:
        feature_order = available_labels
    else:
        missing = [f for f in file_order if f not in available_labels]
        if missing:
            raise ValueError(f"Invalid file_order: {missing} not found in feature_label list")
        feature_order = file_order

    # Step 4: finalize
    finalize_result = finalize(
        database_path=database_path,
        cache_dir=output_dir,
        file_order=feature_order,
        edge_types=edge_types,
        apply_zscore=apply_zscore
    )

    return {
        "common_sample_ids": common_ids,
        "results": results,
        "summary": {
            "total": len(results),
            "success": sum(1 for r in results if r["status"] == "success"),
            "error": sum(1 for r in results if r["status"] == "error")
        },
        "finalized_dataset": finalize_result
    }