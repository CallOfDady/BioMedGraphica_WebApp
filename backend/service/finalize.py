import os
import glob
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

def merge_data_and_generate_entity_mapping(cache_folder, file_order, apply_zscore=False):
    processed_data_path = os.path.join(cache_folder, 'processed_data/')
    os.makedirs(processed_data_path, exist_ok=True)

    print('File order:', file_order)

    # Step 1: Merge npy feature files 
    merged_data = None
    for file_name in file_order:
        npy_file_path = os.path.join(cache_folder, "_x", f"{file_name}.npy")
        if os.path.exists(npy_file_path):
            data_array = np.load(npy_file_path)
            
            if apply_zscore:
                print(f"Applying z-score normalization to {npy_file_path}")
                scaler = StandardScaler()
                data_array = scaler.fit_transform(data_array)

            merged_data = data_array if merged_data is None else np.concatenate((merged_data, data_array), axis=1)
        else:
            print(f"Warning: {npy_file_path} does not exist.")

    if merged_data is None:
        print("No data merged. Exiting.")
        return None, None, processed_data_path

    # Step 2: Save merged feature matrix
    x_all_path = os.path.join(processed_data_path, 'xAll.npy')
    np.save(x_all_path, merged_data)
    print(f"Merged feature matrix saved to: {x_all_path}")

    # Step 3: Load label data (.npy) instead of .csv
    def get_label_npy_path():
        y_folder_path = os.path.join(cache_folder, "_y")
        npy_files = [f for f in os.listdir(y_folder_path) if f.endswith(".npy")]
        if len(npy_files) != 1:
            raise ValueError("Expected exactly one label .npy file in '_y' folder.")
        return os.path.join(y_folder_path, npy_files[0])

    label_npy_path = get_label_npy_path()
    labels = np.load(label_npy_path)
    print(f"Loaded label data from {label_npy_path}")

    y_all_path = os.path.join(processed_data_path, 'yAll.npy')
    np.save(y_all_path, labels)
    print(f"Label matrix saved to: {y_all_path}")

    # Step 4: Load and concatenate ID mapping files
    mapping_dfs = []
    for file_name in file_order:
        mapping_file_path = os.path.join(cache_folder, 'raw_id_mapping', f"{file_name}_id_map.csv")
        if os.path.exists(mapping_file_path):
            df = pd.read_csv(mapping_file_path)
            mapping_dfs.append(df)
        else:
            print(f"Warning: Mapping file {mapping_file_path} not found.")

    full_mapping_df = pd.concat(mapping_dfs, ignore_index=True)
    full_mapping_df["Index"] = range(len(full_mapping_df))
    full_mapping_df = full_mapping_df[["Index", "Original_ID", "BioMedGraphica_Conn_ID"]]

    entity_mapping_path = os.path.join(processed_data_path, 'entity_index_id_mapping.csv')
    full_mapping_df.to_csv(entity_mapping_path, index=False)
    print(f"Entity ID mapping saved to: {entity_mapping_path}")

    return full_mapping_df, merged_data, processed_data_path

def filter_and_save_edge_data(database_path, entity_index_id_mapping):
    """Filter edge data based on entity index and return unique types."""
    edge_csv_path = os.path.join(database_path, 'Relation', 'BioMedGraphica_Conn_Relation.csv')
    edge_data_raw = pd.read_csv(edge_csv_path)

    edge_data = edge_data_raw[['BMGC_From_ID', 'BMGC_To_ID', 'Type']].copy()

    # Filter edge data based on entity_index_id_mapping
    filtered_edge_data = edge_data[
        edge_data['BMGC_From_ID'].isin(entity_index_id_mapping['BioMedGraphica_Conn_ID']) &
        edge_data['BMGC_To_ID'].isin(entity_index_id_mapping['BioMedGraphica_Conn_ID'])
    ]

    # Get unique types from the filtered edge data
    unique_types = filtered_edge_data['Type'].unique().tolist()
    
    return filtered_edge_data, unique_types

def process_edge_data_with_selected_types(filtered_edge_data, selected_types, entity_index_id_mapping, processed_data_path):
    """Process edge data based on selected types and save filtered data."""
    
    # Filter edge data based on selected types
    filtered_edge_data = filtered_edge_data[filtered_edge_data['Type'].isin(selected_types)]
    
    # Create From_Index and To_Index columns
    entity_index = pd.Series(entity_index_id_mapping['Index'].values, index=entity_index_id_mapping['BioMedGraphica_Conn_ID'])
    filtered_edge_data.loc[:, 'From_Index'] = filtered_edge_data['BMGC_From_ID'].map(entity_index)
    filtered_edge_data.loc[:, 'To_Index'] = filtered_edge_data['BMGC_To_ID'].map(entity_index)
    
    # Sort the edge data by From_Index
    filtered_edge_data = filtered_edge_data.sort_values(by=['From_Index'])

    ppi_edge_data = filtered_edge_data[filtered_edge_data["Type"] == "Protein-Protein"]
    internal_edge_data = filtered_edge_data[filtered_edge_data["Type"] != "Protein-Protein"]

    # Save edge_index as a NumPy array
    edge_index = filtered_edge_data[['From_Index', 'To_Index']].T
    np.save(os.path.join(processed_data_path, 'edge_index.npy'), edge_index.to_numpy().astype(np.int64))

    # Export PPI edges
    if not ppi_edge_data.empty:
        ppi_edge_index = ppi_edge_data[['From_Index', 'To_Index']].T.to_numpy().astype(np.int64)
        np.save(os.path.join(processed_data_path, 'ppi_edge_index.npy'), ppi_edge_index)
        print("Saved: ppi_edge_index.npy")

    # Export internal edges
    if not internal_edge_data.empty:
        internal_edge_index = internal_edge_data[['From_Index', 'To_Index']].T.to_numpy().astype(np.int64)
        np.save(os.path.join(processed_data_path, 'internal_edge_index.npy'), internal_edge_index)
        print("Saved: internal_edge_index.npy")

    # Save the filtered edge data with BioMedGraphica_Conn_ID
    filtered_edge_data.to_csv(os.path.join(processed_data_path, 'filtered_edge_id_index_data.csv'), index=False)


def finalize(database_path, cache_dir, file_order, edge_types=None, apply_zscore=False):

    mapping_df, merged_data, out_dir = merge_data_and_generate_entity_mapping(
        cache_dir, file_order, apply_zscore
    )
    if mapping_df is None:
        return {"status": "error", "error": "No data merged"}

    filtered_edge_data, unique_types = filter_and_save_edge_data(database_path, mapping_df)

    if edge_types is None:
        selected = unique_types
    else:
        selected = [t for t in edge_types if t in unique_types]

    process_edge_data_with_selected_types(
        filtered_edge_data,
        selected,
        mapping_df,
        out_dir,
    )

    return {
        "status": "success",
        "processed_data_path": out_dir,
        "selected_edge_types": selected,
        "available_edge_types": unique_types,
    }