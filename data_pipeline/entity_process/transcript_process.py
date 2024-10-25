# transcript_process.py

import pandas as pd
import numpy as np

def process_transcript(entity_type, id_type, file_path, selected_column, feature_label):
    """Process Transcript data."""
    print(f"Processing Transcript: {entity_type}, ID Type: {id_type}, File: {file_path}, Column: {selected_column}")
    
    transcript_entity_data = pd.read_csv('resources/database/BioMedGraphica/Node/Transcript/biomedgraphica_transcript.csv')

    # Determine the separator based on the file extension
    if file_path.endswith('.txt') or file_path.endswith('.tsv'):
        sep = '\t'
    elif file_path.endswith('.csv'):
        sep = ','
    else:
        raise ValueError("Unsupported file type. Please provide a .txt, .tsv, or .csv file.") 

    def process_gene_expression(transcript_entity_data):
        """Process Gene Expression data, map Sample_ID to MedGraphica_ID, and export mapping."""
        print(f"Processing Gene Expression for {entity_type} with Feature Label: {feature_label}")

        # Read the gene expression file (already in the format Sample_ID | Gene1 | Gene2 | ...)
        gene_expression = pd.read_csv(file_path, sep=sep)

        # Step 1: Transpose the gene expression data to Gene_Name | S1 | S2 | ... format
        gene_expression_transposed = gene_expression.set_index(selected_column).T.reset_index()
        gene_expression_transposed.rename(columns={'index': id_type}, inplace=True)

        # Step 2: Merge with transcript_entity_data to map to MedGraphica_ID
        transcript_entity_data = transcript_entity_data[[id_type, 'BioMedGraphica_ID']].copy()

        # Merge the gene expression data with the transcript entity data on id_type
        gene_expression_merged = pd.merge(
            gene_expression_transposed,
            transcript_entity_data,
            on=id_type,
            how='inner'
        )

        # Step 3: Extract the id_type and MedGraphica_ID columns as the mapping table
        # This will create a mapping between the original id_type (e.g., Gene_Name) and MedGraphica_ID
        mapping_table = gene_expression_merged[[id_type, 'BioMedGraphica_ID']].drop_duplicates()
        mapping_table = mapping_table.rename(columns={id_type: 'Original_ID'})

        # Save the mapping table to a separate CSV file
        map_output_file = f'cache/raw_id_mapping/{feature_label.lower()}_id_map.csv'
        mapping_table.to_csv(map_output_file, sep=",", index=False)

        # Step 4: Drop the 'id_type' column after merging
        gene_expression_merged.drop(columns=[id_type], inplace=True)

        # Step 5: Ensure 'BioMedGraphica_ID' is the first column
        cols = ['BioMedGraphica_ID'] + [col for col in gene_expression_merged.columns if col not in ['BioMedGraphica_ID']]
        gene_expression_data = gene_expression_merged[cols]

        # Select numeric columns (which are now samples, i.e., S1, S2, etc.)
        numeric_cols = gene_expression_data.select_dtypes(include=[np.number]).columns.tolist()

        # Group by 'BioMedGraphica_ID' and calculate the mean for all numeric columns
        gene_expression_data.loc[:, numeric_cols] = gene_expression_data[numeric_cols].fillna(0)
        gene_expression_data = gene_expression_data.groupby('BioMedGraphica_ID')[numeric_cols].mean()

        # Reset the index to turn 'BioMedGraphica_ID' back into a column
        gene_expression_data.reset_index(inplace=True)

        # Step 6: Transpose the data back to the original format (Sample_ID | Gene1 | Gene2 | ...)
        gene_expression_final = gene_expression_data.set_index('BioMedGraphica_ID').T.reset_index()
        gene_expression_final.rename(columns={'index': selected_column}, inplace=True)

        # Export the final processed gene expression data to a CSV file
        output_file_path = f'cache/{feature_label.lower()}.csv'
        gene_expression_final.to_csv(output_file_path, sep=",", index=False)

        print(f"Gene expression data processing completed. Output saved to {output_file_path}")
        print(f"id_type to MedGraphica_ID mapping saved to {map_output_file}")




    # Check if the feature_label contains "expression" or "cnv"
    if "expression" in feature_label.lower():
        process_gene_expression(transcript_entity_data)
    elif "xxx" in feature_label.lower():
        print(f"Processing xxx data for Transcript: {entity_type} with Feature Label: {feature_label}")
    else:
        print(f"Processing for Feature Label: {feature_label} is not implemented yet.")
        # Leave space for other feature_label handling in the future


# Example usage:
# process_transcript('Transcript', 'Ensembl_Gene_ID', 'E:/LabWork/MedGraphica_GUI/test_data/gene_expression.csv', 'Patient_ID', 'gene_expression')
