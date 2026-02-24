import os
import pandas as pd
import numpy as np
import json

from backend.service.matcher_loader import load_matcher
from backend.utils.io import _load_bmg_conn_ids, save_name_and_desc

def generate_soft_match_candidates(
    entity_type,
    file_path,
    feature_label,
    database_path,
    topk=5,
    output_path=None,
    matcher_index_root_dir=None,
    matcher_device="cpu",
    matcher_model_path="dmis-lab/biobert-base-cased-v1.2",
):
    entity_type = entity_type.capitalize()

    matcher = load_matcher(
        entity_type=entity_type,
        index_root_dir=matcher_index_root_dir,
        device=matcher_device,
        model_path=matcher_model_path,
    )

    sep = "\t" if file_path.endswith((".tsv", ".txt")) else ","
    df = pd.read_csv(file_path, sep=sep)
    df.rename(columns={df.columns[0]: "Sample_ID"}, inplace=True)

    melted = df.melt(id_vars="Sample_ID", var_name="Original_ID", value_name="value")
    used_ids = sorted(set(melted["Original_ID"].astype(str)))

    raw_results = matcher.match_many(
        queries=used_ids,
        topk=topk,
        top_alias=200,
        method="max",
        return_alias_hits=0,
        enable_exact=True,
        exact_score=1.0,
    )

    mapping_data = {}
    for oid in used_ids:
        results = raw_results.get(oid, [])

        mapping_data[oid] = results

    if output_path:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(mapping_data, f, indent=2, ensure_ascii=False)

    return {
        "feature_label": feature_label,
        "entity_type": entity_type,
        "total_original_ids": len(used_ids),
        "candidates": mapping_data,
    }

def apply_soft_match_selection(
    entity_type,
    file_path,
    feature_label,
    database_path,
    sample_ids,
    user_selections: dict,  # { Original_ID: BioMedGraphica_Conn_ID or None }
    output_dir="cache"
):
    entity_type = entity_type.capitalize()

    bmg_ids = _load_bmg_conn_ids(database_path, entity_type)

    os.makedirs(os.path.join(output_dir, "_x"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "raw_id_mapping"), exist_ok=True)

    sep = "\t" if file_path.endswith((".tsv", ".txt")) else ","
    df = pd.read_csv(file_path, sep=sep)
    df.rename(columns={df.columns[0]: "Sample_ID"}, inplace=True)
    df["Sample_ID"] = df["Sample_ID"].astype(str)

    melted = df.melt(id_vars="Sample_ID", var_name="Original_ID", value_name="value")
    used_ids = sorted(set(melted["Original_ID"]))

    # Build raw mapping based on user selections
    mapping_df = pd.DataFrame(
        [
            {"Original_ID": oid, "BioMedGraphica_Conn_ID": bmg_id}
            for oid, bmg_id in user_selections.items()
            if bmg_id  # not None / not empty
        ],
        columns=["Original_ID", "BioMedGraphica_Conn_ID"],  # keep schema even when empty
    )

    # If nothing selected, still write full raw_id_mapping file and zero matrix
    if mapping_df.empty:
        final_mapping_df = pd.DataFrame({
            "BioMedGraphica_Conn_ID": bmg_ids,
            "Original_ID": [""] * len(bmg_ids)
        })

        final_mapping_df.to_csv(
            os.path.join(output_dir, "raw_id_mapping", f"{feature_label.lower()}_id_map.csv"),
            index=False
        )

        data_matrix = pd.DataFrame(0, index=sample_ids, columns=bmg_ids)
        np.save(os.path.join(output_dir, "_x", f"{feature_label.lower()}.npy"), data_matrix.values)

        # Optional but recommended: still save names/descriptions for consistency
        save_name_and_desc(
            database_path,
            entity_type,
            output_dir,
            feature_label
        )

        return {
            "feature_label": feature_label,
            "mapped_count": 0,
            "status": "success",
            "message": "No mappings selected"
        }

    # Group original IDs per BMG ID
    grouped_mapping_df = (
        mapping_df.groupby("BioMedGraphica_Conn_ID")["Original_ID"]
        .apply(lambda x: ";".join(sorted(set(str(i) for i in x if pd.notna(i) and str(i).strip()))))
        .reset_index()
    )

    # Ensure full list of BMG IDs included
    final_mapping_df = pd.DataFrame({"BioMedGraphica_Conn_ID": bmg_ids}).merge(
        grouped_mapping_df, on="BioMedGraphica_Conn_ID", how="left"
    ).fillna({"Original_ID": ""})

    final_mapping_df.to_csv(
        os.path.join(output_dir, "raw_id_mapping", f"{feature_label.lower()}_id_map.csv"),
        index=False
    )

    if mapping_df.empty:
        data_matrix = pd.DataFrame(0, index=sample_ids, columns=bmg_ids)
        np.save(os.path.join(output_dir, "_x", f"{feature_label.lower()}.npy"), data_matrix.values)
        return {
            "feature_label": feature_label,
            "mapped_count": 0,
            "status": "success",
            "message": "No mappings selected"
        }

    melted["Original_ID"] = melted["Original_ID"].astype(str)
    mapping_df["Original_ID"] = mapping_df["Original_ID"].astype(str)

    merged = pd.merge(melted, mapping_df, on="Original_ID", how="inner")
    merged["value"] = pd.to_numeric(merged["value"], errors="coerce")
    merged = merged.dropna(subset=["value"])

    if merged.empty:
        return {
            "feature_label": feature_label,
            "mapped_count": 0,
            "status": "error",
            "error": "No valid numeric data after merging"
        }

    expr = merged.pivot_table(
        index="Sample_ID",
        columns="BioMedGraphica_Conn_ID",
        values="value",
        fill_value=0,
        aggfunc="mean"
    )

    expr = expr.reindex(index=sample_ids, columns=bmg_ids, fill_value=0)
    np.save(os.path.join(output_dir, "_x", f"{feature_label.lower()}.npy"), expr.values)

    save_name_and_desc(
        database_path,
        entity_type,
        output_dir,
        feature_label
    )

    return {
        "feature_label": feature_label,
        "mapped_count": len(mapping_df),
        "status": "success"
    }