import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from backend.finalize import finalize

__all__ = ["process"]

def _read_mapping(database_path, entity_type):
    path = os.path.join(
        database_path,
        "Entity",
        entity_type,
        f"BioMedGraphica_Conn_{entity_type}.csv",
    )
    if not os.path.exists(path):
        raise FileNotFoundError(f"Mapping file not found: {path}")
    return pd.read_csv(path)

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

    if (fill0) and id_type:
        return {"feature_label": feature_label, "status": "error", "error": "id_type must be empty for fill0"}

    try:
        if match_mode == "hard":
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
            return _process_soft_entity(cfg, common_ids, database_path, output_dir)
        else:
            return {
                "feature_label": feature_label,
                "status": "error",
                "error": f"Unknown match_mode '{match_mode}', expected 'hard' or 'soft'"
            }

    except Exception as e:
        return {"feature_label": feature_label, "status": "error", "error": str(e)}

def _process_soft_entity(cfg, sample_ids, database_path, output_dir):
    entity_type = cfg["entity_type"].lower()
    if entity_type == "disease":
        return process_entity_soft_match(
            entity_type=cfg["entity_type"],
            id_type=cfg.get("id_type", ""),
            file_path=cfg["file_path"],
            feature_label=cfg["feature_label"],
            database_path=database_path,
            sample_ids=sample_ids,
            output_dir=output_dir
        )
    else:
        return {
            "feature_label": cfg.get("feature_label"),
            "status": "error",
            "error": f"Soft match not implemented for entity_type='{entity_type}'"
        }

def process_entity_hard_match(entity_type, id_type, file_path, feature_label, database_path, fill0=False, sample_ids=None, output_dir="cache"):
    entity_type = entity_type.capitalize()
    entity_data = _read_mapping(database_path, entity_type)
    bmg_ids = entity_data["BioMedGraphica_Conn_ID"].drop_duplicates().tolist()

    os.makedirs(os.path.join(output_dir, "_x"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "raw_id_mapping"), exist_ok=True)

    if fill0:
        print(f"Filling zeros for {feature_label} with {len(sample_ids)}samples and {len(bmg_ids)} BioMedGraphica IDs...")
        if sample_ids is None:
            raise ValueError("sample_ids must be provided when fill0=True")
        data_matrix = pd.DataFrame(0, index=sample_ids, columns=bmg_ids)
        data_matrix.index.name = "Sample_ID"
        data_matrix.reset_index(inplace=True)
        data_matrix["Sample_ID"] = data_matrix["Sample_ID"].astype(str)
        np.save(os.path.join(output_dir, "_x", f"{feature_label.lower()}.npy"), data_matrix.drop(columns=["Sample_ID"]).values)
        # data_matrix.to_csv(os.path.join(output_dir, "_x", f"{feature_label.lower()}.csv"), index=False)
        mapping_df = pd.DataFrame({
            "BioMedGraphica_Conn_ID": bmg_ids,
            "Original_ID": ["" for _ in bmg_ids],
        })
        mapping_df.to_csv(os.path.join(output_dir, "raw_id_mapping", f"{feature_label.lower()}_id_map.csv"), index=False)
        return {"feature_label": feature_label, "status": "success"}

    sep = "\t" if file_path.endswith((".tsv", ".txt")) else ","
    df = pd.read_csv(file_path, sep=sep)
    df.rename(columns={df.columns[0]: "Sample_ID"}, inplace=True)
    df["Sample_ID"] = df["Sample_ID"].astype(str)

    melted = df.melt(id_vars="Sample_ID", var_name="Original_ID", value_name="value")
    used_ids = set(df.columns) - {"Sample_ID"}

    mapping_raw = entity_data[[id_type, "BioMedGraphica_Conn_ID"]].dropna()
    mapping_raw[id_type] = mapping_raw[id_type].astype(str).str.strip()
    mapping_expanded = mapping_raw.assign(Original_ID=mapping_raw[id_type].str.split(";")).explode("Original_ID")
    mapping_expanded["Original_ID"] = mapping_expanded["Original_ID"].str.strip()
    mapping_df = mapping_expanded[mapping_expanded["Original_ID"].isin(used_ids)]
    mapping_df = mapping_df[["Original_ID", "BioMedGraphica_Conn_ID"]].drop_duplicates()

    print(f"[DEBUG] mapping_df rows: {len(mapping_df)}")

    merged = pd.merge(melted, mapping_df, on="Original_ID", how="inner")

    print(f"[DEBUG] merged shape: {merged.shape}")

    expr = merged.pivot_table(index="Sample_ID", columns="BioMedGraphica_Conn_ID", values="value", fill_value=0)
    
    # print(f"[DEBUG] Before reindex - expr shape: {expr.shape}")
    # print(f"[DEBUG] expr.index (first 5): {list(expr.index[:5])}")
    # print(f"[DEBUG] sample_ids (first 5): {sample_ids[:5]}")
    # print(f"[DEBUG] expr non-zero values count: {(expr != 0).sum().sum()}")

    common_samples = set(expr.index) & set(sample_ids)
    # print(f"[DEBUG] Common samples count: {len(common_samples)} / {len(sample_ids)}")
    
    expr = expr.reindex(index=sample_ids, columns=bmg_ids, fill_value=0)
    
    # print(f"[DEBUG] After reindex - expr shape: {expr.shape}")
    # print(f"[DEBUG] expr non-zero values count: {(expr != 0).sum().sum()}")


    np.save(os.path.join(output_dir, "_x", f"{feature_label.lower()}.npy"), expr.values)
    # expr.to_csv(os.path.join(output_dir, "_x", f"{feature_label.lower()}.csv"))

    grouped_mapping_df = (
        mapping_df.groupby("BioMedGraphica_Conn_ID")["Original_ID"]
        .apply(lambda x: ";".join(sorted(set(str(i) for i in x if pd.notna(i) and str(i).strip()))))
        .reset_index()
    )
    final_mapping_df = pd.DataFrame({"BioMedGraphica_Conn_ID": bmg_ids}).merge(
        grouped_mapping_df, on="BioMedGraphica_Conn_ID", how="left"
    ).fillna({"Original_ID": ""})

    final_mapping_df.to_csv(os.path.join(output_dir, "raw_id_mapping", f"{feature_label.lower()}_id_map.csv"), index=False)
    return {"feature_label": feature_label, "status": "success"}

def process_entity_soft_match(entity_type, id_type, file_path, feature_label, database_path, sample_ids, output_dir):
    return {
        "feature_label": feature_label,
        "status": "error",
        "error": f"Soft match for entity_type='{entity_type}' is not implemented yet"
    }

def process(*configs, database_path, output_dir, file_order=None, apply_zscore=False, edge_types=None):
    common_ids = _compute_common_sample_ids(configs)
    results = []

    # Step 1: process labels
    for cfg in [c for c in configs if c["entity_type"].lower() == "label"]:
        results.append(_process_label(cfg, common_ids, output_dir))

    # Step 2: process omics entities
    omics_cfgs = [c for c in configs if c["entity_type"].lower() != "label"]
    for cfg in tqdm(omics_cfgs, desc="Processing", unit="entity"):
        results.append(_process_omics_entity(cfg, common_ids, database_path, output_dir))

    # Step 3: prepare feature_order
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