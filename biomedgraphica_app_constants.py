from typing import Dict, List

# --------------------------- CONSTANTS -----------------------------------
ENTITY_TYPES = [
    "", "Disease","Drug","Exposure","Gene","Metabolite","Microbiota",
    "Pathway","Phenotype","Promoter","Protein","Transcript",
]
ID_TYPES: Dict[str, List[str]] = {
    "": [""],
    "Gene": ["Ensembl_Gene_ID","Locus-based ID","HGNC_Symbol","Ensembl_Gene_ID_Version","HGNC_ID","OMIM_ID","NCBI_ID","RefSeq_ID","GO_ID"],
    "Transcript": ["Ensembl_Transcript_ID","Ensembl_Transcript_ID_Version","Ensembl_Gene_ID","Reactome_ID","RefSeq_ID","RNACentral_ID"],
    "Protein": ["Ensembl_Protein_ID","Ensembl_Protein_ID_Version","RefSeq_ID","Uniprot_ID","HGNC_Symbol"],
    "Promoter": ["Ensembl_Gene_ID","HGNC_Symbol","Ensembl_Gene_ID_Version","HGNC_ID","OMIM_ID","NCBI_ID","RefSeq_ID","GO_ID"],
    "Drug": ["PubChem_CID_ID","PubChem_SID_ID","CAS_ID","NDC_ID","UNII_ID","InChI_ID","ChEBI_ID","DrugBank_ID"],
    "Disease": ["OMIM_ID","ICD11_ID","ICD10_ID","DO_ID","SnomedCT_ID","UMLS_ID","MeSHID","Mondo_ID"],
    "Phenotype": ["Phenotype_Name","HPO_ID","OMIM_ID","Orpha_ID","UMLS_ID"],
    "MicroBiome": ["NCBI_ID","SILVA_ID","Greengenes_ID","RDP_ID","RNACentral_ID","GTDB_ID"],
}
DEFAULT_FILE_ORDER = ["promoter","gene","transcript","protein"]
DEFAULT_EDGE_TYPES = ["Gene-Transcript","Promoter-Gene","Protein-Protein","Transcript-Protein"]
