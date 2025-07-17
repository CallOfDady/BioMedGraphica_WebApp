import os
import pandas as pd
import numpy as np
import torch
import streamlit as st

def _load_bmg_embeddings(database_path, entity_type):
    path = os.path.join(
        database_path,
        "Embed",
        entity_type,
        f"{entity_type}_embeddings.pt",
    )
    print(f"Looking for embeddings at: {path}")
    if not os.path.exists(path):
        print(f"Embedding file not found: {path}")
        raise FileNotFoundError(f"Embedding file not found: {path}")
    print(f"Found embeddings file: {path}")
    return torch.load(path, map_location=torch.device('cpu'))


def process_entity_soft_match(
    entity_type,
    file_path,
    feature_label,
    database_path,
    sample_ids,
    topk=5,
    output_dir="cache",
    interactive_mode=True,
):
    print(f" Processing soft match for {entity_type}...")
    print(f"  - file_path: {file_path}")
    print(f"  - feature_label: {feature_label}")
    print(f"  - interactive_mode: {interactive_mode}")

    # Import here to avoid circular import
    from utils.app_init import load_matcher
    
    matcher = load_matcher()
    entity_type = entity_type.capitalize()
    embeddings = _load_bmg_embeddings(database_path, entity_type)
    bmg_ids = list(embeddings.keys())

    os.makedirs(os.path.join(output_dir, "_x"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "raw_id_mapping"), exist_ok=True)

    sep = "\t" if file_path.endswith((".tsv", ".txt")) else ","
    df = pd.read_csv(file_path, sep=sep)
    df.rename(columns={df.columns[0]: "Sample_ID"}, inplace=True)
    df["Sample_ID"] = df["Sample_ID"].astype(str)

    melted = df.melt(id_vars="Sample_ID", var_name="Original_ID", value_name="value")
    used_ids = sorted(set(melted["Original_ID"]))

    id_to_bmg = {}
    bmg_to_original = {bmg_id: "" for bmg_id in bmg_ids}

    # Handle interactive mode (default for soft matching)
    if interactive_mode:
        # Create a unique key for this mapping session based on entity type and feature label
        mapping_session_key = f"mapping_session_{entity_type}_{feature_label}"
        
        print(f"Looking for mapping session: {mapping_session_key}")
        
        # Check if already have completed mappings for this session
        if mapping_session_key in st.session_state:
            session_data = st.session_state[mapping_session_key]
            print(f" Found existing session: completed={session_data.get('completed', False)}")
            
            if session_data.get("completed", False):
                print(f" Using previously completed mappings for {entity_type}")
                user_selections = session_data["selections"]
                print(f" User selections: {user_selections}")
                
                # Apply user selections
                for oid, selected_bmg in user_selections.items():
                    if selected_bmg is not None:
                        id_to_bmg[oid] = selected_bmg
                        bmg_to_original[selected_bmg] = oid
                        print(f"  - Applied: {oid} -> {selected_bmg}")
                    else:
                        # User selected "No Match" for this ID
                        print(f"  - Skipped (No Match): {oid}")
            else:
                # User is still in the process of making selections
                print(f"Waiting for user selections for {entity_type}...")
                # Don't show UI here - it will be handled by the collapsible component
                return {
                    "feature_label": feature_label,
                    "mapped_count": 0,
                    "total_original_ids": len(used_ids),
                    "status": "pending_user_selection",
                    "message": f"Waiting for user to complete {entity_type} mappings"
                }
        else:
            # First time - collect mappings 
            print(f"First time processing {entity_type}, collecting mappings...")
            
            # Collect all mappings
            mapping_data = {}
            for oid in used_ids:
                candidates = matcher.get_topk_entities(query=oid, k=topk, embeddings=embeddings)
                mapping_data[oid] = candidates
            
            # Store mapping data in session state
            st.session_state[mapping_session_key] = {
                "mapping_data": mapping_data,
                "entity_type": entity_type,
                "feature_label": feature_label,
                "completed": False,
                "selections": {}
            }
            
            # Return pending status to show UI
            return {
                "feature_label": feature_label,
                "mapped_count": 0,
                "total_original_ids": len(used_ids),
                "status": "pending_user_selection",
                "message": f"Waiting for user to complete {entity_type} mappings"
            }
    else:
        # Non-interactive mode - use first candidate
        print(f"Non-interactive mode: using first candidate for each ID")
        for oid in used_ids:
            candidates = matcher.get_topk_entities(query=oid, k=topk, embeddings=embeddings)
            if candidates:
                selected_bmg = candidates[0][0]  # Take first candidate
                id_to_bmg[oid] = selected_bmg
                bmg_to_original[selected_bmg] = oid

    # Create mapping DataFrame
    mapping_df = pd.DataFrame([
        {"Original_ID": oid, "BioMedGraphica_Conn_ID": bmg_id}
        for oid, bmg_id in id_to_bmg.items()
    ])

    print(f"Mapping DataFrame shape: {mapping_df.shape}")
    print(f"Total original IDs: {len(used_ids)}")
    print(f"Successfully mapped IDs: {len(id_to_bmg)}")
    print(f"Unmapped IDs: {len(used_ids) - len(id_to_bmg)}")
    
    # Always save the mapping file, even if empty
    if len(id_to_bmg) > 0:
        bmg_ids = list(id_to_bmg.values())
        final_mapping_df = pd.DataFrame({
            "BioMedGraphica_Conn_ID": bmg_ids,
            "Original_ID": [bmg_to_original[bmg_id] for bmg_id in bmg_ids],
        })
    else:
        # Create empty mapping table if no mappings were selected
        # But still include all BMG IDs with empty Original_ID
        final_mapping_df = pd.DataFrame({
            "BioMedGraphica_Conn_ID": bmg_ids,
            "Original_ID": ["" for _ in bmg_ids],
        })
        print(" No mappings selected - saving mapping table with empty Original_IDs")
    
    # Save the mapping table regardless of whether it's empty
    final_mapping_df.to_csv(os.path.join(output_dir, "raw_id_mapping", f"{feature_label.lower()}_id_map.csv"), index=False)
    
    # If no mappings were selected, handle gracefully
    if len(id_to_bmg) == 0:
        print(" No mappings selected - creating zero-filled feature matrix")
        # Create zero-filled feature matrix with same structure as hard_match fill0 mode
        data_matrix = pd.DataFrame(0, index=sample_ids, columns=bmg_ids)
        np.save(os.path.join(output_dir, "_x", f"{feature_label.lower()}.npy"), data_matrix.values)
        
        return {
            "feature_label": feature_label,
            "mapped_count": 0,
            "total_original_ids": len(used_ids),
            "status": "success",
            "message": f"Processing completed with no mappings selected for {feature_label}"
        }
    
    print(f"Melted DataFrame shape: {melted.shape}")
    print(f"Melted DataFrame dtypes:\n{melted.dtypes}")
    
    # Ensure Original_ID columns are the same type for merging
    melted["Original_ID"] = melted["Original_ID"].astype(str)
    mapping_df["Original_ID"] = mapping_df["Original_ID"].astype(str)
    
    merged = pd.merge(melted, mapping_df, on="Original_ID", how="inner")
    print(f"Merged DataFrame shape: {merged.shape}")
    
    if merged.empty:
        print("No matches found after merging - check mapping results")
        return {
            "feature_label": feature_label,
            "mapped_count": 0,
            "total_original_ids": len(used_ids),
            "status": "error",
            "error": "No matches found after applying user mappings"
        }
    
    print(f"Merged DataFrame dtypes:\n{merged.dtypes}")
    print(f"Sample of merged data:\n{merged.head()}")
    
    # Ensure value column is numeric before pivot
    print(f"Converting value column to numeric...")
    merged["value"] = pd.to_numeric(merged["value"], errors="coerce")
    
    # Handle any NaN values that might have been introduced
    nan_count = merged["value"].isna().sum()
    if nan_count > 0:
        print(f"Found {nan_count} NaN values after conversion, dropping them")
        merged = merged.dropna(subset=["value"])
    
    print(f"After cleaning - Merged DataFrame shape: {merged.shape}")
    
    if merged.empty:
        print("No data left after cleaning")
        return {
            "feature_label": feature_label,
            "mapped_count": 0,
            "total_original_ids": len(used_ids),
            "status": "error",
            "error": "No valid numeric data found after cleaning"
        }
    
    try:
        expr = merged.pivot_table(index="Sample_ID", columns="BioMedGraphica_Conn_ID", values="value", fill_value=0, aggfunc="mean")
        print(f"Pivot table created successfully with shape: {expr.shape}")
    except Exception as e:
        print(f"Error creating pivot table: {e}")
        print(f"Merged DataFrame sample:\n{merged.head()}")
        print(f"Unique BioMedGraphica_Conn_ID values: {merged['BioMedGraphica_Conn_ID'].unique()}")
        return {
            "feature_label": feature_label,
            "mapped_count": 0,
            "total_original_ids": len(used_ids),
            "status": "error",
            "error": f"Error creating pivot table: {e}"
        }
    
    expr = expr.reindex(index=sample_ids, columns=bmg_ids, fill_value=0)

    np.save(os.path.join(output_dir, "_x", f"{feature_label.lower()}.npy"), expr.values)

    return {
        "feature_label": feature_label,
        "mapped_count": len(mapping_df),
        "total_original_ids": len(used_ids),
        "status": "success"
    }
