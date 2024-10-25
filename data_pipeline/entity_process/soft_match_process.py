import pandas as pd

def process_entities(entity_type, id_type, file_path, selected_column, feature_label, matcher, embeddings, selection_callback=None):
    """
    Process entities (Phenotype, Disease, Drug, etc.), allow user selection, and perform further processing.
    """
    print(f"Processing {entity_type}: ID Type: {id_type}, File: {file_path}, Column: {selected_column}")

    # Determine the separator based on the file extension
    if file_path.endswith('.txt') or file_path.endswith('.tsv'):
        sep = '\t'
    elif file_path.endswith('.csv'):
        sep = ','
    else:
        raise ValueError("Unsupported file type. Please provide a .txt, .tsv, or .csv file.")

    # Read the data file
    data_frame = pd.read_csv(file_path, sep=sep)

    # Initialize an empty dictionary to store the topk entities for each column (except the selected column)
    all_topk_entities = {}

    # Get the column names except the selected column
    columns_to_process = [col for col in data_frame.columns if col != selected_column]

    print(f"Columns to process: {columns_to_process}")

    # Get topk matches for each column (except selected_column)
    for column in columns_to_process:
        # Ensure column name is a string (it should be, but just in case)
        column_name_str = str(column)
        
        # Get top 3 entity matches for the column name itself
        topk_entities = matcher.get_topk_entities(query=column_name_str, k=3, embeddings=embeddings)
        
        # Store the topk matches for this column name
        all_topk_entities[column] = topk_entities
        print(f"Top matches for column {column}: {all_topk_entities[column]}")


    # Allow user selection of the topk entities
    if selection_callback:
        updated_topk_entities = selection_callback(all_topk_entities, entity_type, id_type, file_path, selected_column, feature_label, data_frame)
        if updated_topk_entities is not None:
            all_topk_entities = updated_topk_entities
        else:
            print("Warning: selection_callback returned None")

    return all_topk_entities  # Return selected entities for further processing


def process_entities_file(entity_type, id_type, feature_label, data_frame, selected_column, selected_entities):
    """
    Process the selected entities and update the DataFrame.
    Replace column names (except the selected column) with the selected match term (e.g., hpo_term or drug term)
    and add a MedGraphica_ID column with corresponding med_id for each selected match.
    """
    data_frame_copy = data_frame.copy()

    # Create an empty list to store mapping information
    mapping = []

    # Iterate over the selected entities and update column names
    for column, selected_matches in selected_entities.items():
        med_id, term = selected_matches[0]  # Get the first match (top-1)

        # Replace the column name with the selected MedGraphica_ID (med_id) and store the mapping
        if column in data_frame_copy.columns:
            # Rename the column using the med_id instead of term
            data_frame_copy = data_frame_copy.rename(columns={column: med_id})
            # Store the mapping of original column, med_id, and term
            mapping.append([column, med_id, term])
            print(f"Replaced column {column} with {med_id}")

    # Convert the mapping list to a DataFrame
    mapping_df = pd.DataFrame(mapping, columns=['Original_Column', 'BioMedGraphica_ID', 'Mapped_Term'])

    # Save the mapping table to a separate CSV file
    map_output_file = f'cache/raw_id_mapping/{feature_label.lower()}_id_map.csv'
    mapping_df.to_csv(map_output_file, sep=",", index=False)
    print(f"Mapping table saved to {map_output_file}")

    # Save the updated DataFrame to a CSV file
    output_file_path = f'cache/{feature_label.lower()}.csv'
    data_frame_copy.to_csv(output_file_path, index=False)
    print(f"Processed entity data saved to {output_file_path}")