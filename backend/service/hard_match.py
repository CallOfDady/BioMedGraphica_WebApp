import os
import pandas as pd
import numpy as np

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

def process_entity_hard_match(entity_type, id_type, file_path, feature_label, database_path, fill0=False, sample_ids=None, output_dir="cache"):
    entity_type = entity_type.capitalize()
    entity_data = _load_bmg_csv(database_path, entity_type)
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