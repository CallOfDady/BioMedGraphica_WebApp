# gene_process.py

import pandas as pd
import numpy as np

def process_gene(entity_type, id_type, file_path, selected_column, feature_label):
    """Process Gene data."""
    print(f"Processing Gene: {entity_type}, ID Type: {id_type}, File: {file_path}, Column: {selected_column}, Feature Label: {feature_label}")
    
    # Load the gene entity data
    gene_entity_data = pd.read_csv('resources/database/BioMedGraphica/Node/Gene/biomedgraphica_gene.csv')    
        
    # Determine the separator based on the file extension
    if file_path.endswith('.txt') or file_path.endswith('.tsv'):
        sep = '\t'
    elif file_path.endswith('.csv'):
        sep = ','
    else:
        raise ValueError("Unsupported file type. Please provide a .txt, .tsv, or .csv file.")

    def process_gene_expression(gene_entity_data):
        """Process Gene Expression data."""
        print(f"Processing Gene Expression for {entity_type} with Feature Label: {feature_label}")
        print("Not implemented yet. Use transcriptomics entity instead.")

    def process_gene_cnv(gene_entity_data):
        """Process Gene CNV data, map Sample_ID to MedGraphica_ID, and export mapping."""
        print(f"Processing Gene CNV for {entity_type} with Feature Label: {feature_label}")

        # Step 1: Read the CNV file (in the format Sample_ID | Gene1 | Gene2 | ...)
        cnv = pd.read_csv(file_path, sep=sep)

        # Step 2: Transpose the CNV data to Gene_Name | S1 | S2 | ... format
        cnv_transposed = cnv.set_index(selected_column).T.reset_index()
        cnv_transposed.rename(columns={'index': id_type}, inplace=True)

        # Step 3: Merge with gene_entity_data to map to MedGraphica_ID
        gene_entity_data = gene_entity_data[[id_type, 'BioMedGraphica_ID']].copy()

        # Merge the CNV data with the gene entity data on id_type
        cnv_merged = pd.merge(
            cnv_transposed,
            gene_entity_data,
            on=id_type,
            how='inner'
        )

        # Step 4: Extract the id_type and MedGraphica_ID columns as the mapping table
        # This will create a mapping between the original id_type (e.g., Gene_Name) and MedGraphica_ID
        mapping_table = cnv_merged[[id_type, 'BioMedGraphica_ID']].drop_duplicates()
        mapping_table = mapping_table.rename(columns={id_type: 'Original_ID'})
    
        # Save the mapping table to a separate CSV file
        map_output_file = f'cache/raw_id_mapping/{feature_label.lower()}_id_map.csv'
        mapping_table.to_csv(map_output_file, sep=",", index=False)
        print(f"mapping saved to {map_output_file}")

        # Step 5: Drop the 'id_type' column after merging
        cnv_merged.drop(columns=[id_type], inplace=True)

        # Step 6: Ensure 'BioMedGraphica_ID' is the first column
        cols = ['BioMedGraphica_ID'] + [col for col in cnv_merged.columns if col not in ['BioMedGraphica_ID']]
        cnv_data = cnv_merged[cols]

        # Select numeric columns (which are now samples, i.e., S1, S2, etc.)
        numeric_cols = cnv_data.select_dtypes(include=[np.number]).columns.tolist()

        # Group by 'BioMedGraphica_ID' and calculate the mean for all numeric columns
        cnv_data.loc[:, numeric_cols] = cnv_data[numeric_cols].fillna(0)
        cnv_data = cnv_data.groupby('BioMedGraphica_ID')[numeric_cols].mean()

        # Reset the index to turn 'BioMedGraphica_ID' back into a column
        cnv_data.reset_index(inplace=True)

        # Step 7: Transpose the data back to the original format (Sample_ID | Gene1 | Gene2 | ...)
        cnv_final = cnv_data.set_index('BioMedGraphica_ID').T.reset_index()
        cnv_final.rename(columns={'index': selected_column}, inplace=True)

        # Export the final processed CNV data to a CSV file
        output_file_path = f'cache/{feature_label.lower()}.csv'
        cnv_final.to_csv(output_file_path, sep=",", index=False)

        print(f"CNV data processing completed. Output saved to {output_file_path}")

    # Check if the feature_label contains "expression" or "cnv"
    if "expression" in feature_label.lower():
        process_gene_expression(gene_entity_data)
    elif "cnv" in feature_label.lower():
        process_gene_cnv(gene_entity_data)
    else:
        print(f"Processing for Feature Label: {feature_label} is not implemented yet.")
        # Leave space for other feature_label handling in the future