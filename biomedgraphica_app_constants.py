from typing import Dict, List

# --------------------------- CONSTANTS -----------------------------------
ENTITY_TYPES = [
    "", "Promoter", "Gene", "Transcript", "Protein", "Pathway", "Metabolite", "Microbiota", "Exposure","Phenotype", "Disease", "Drug", 
]
ID_TYPES: Dict[str, List[Dict[str, str]]] = {
    "": [{"display_id": "", "actual_id": "", "match_mode": "hard"}],
    "Gene": [
        {"display_id": "HGNC Symbol", "actual_id": "HGNC_Symbol", "match_mode": "hard"},
        {"display_id": "Ensembl Gene ID", "actual_id": "Ensembl_Gene_ID", "match_mode": "hard"},
        {"display_id": "Ensembl Gene ID Version", "actual_id": "Ensembl_Gene_ID_Version", "match_mode": "hard"},
        {"display_id": "NCBI ID", "actual_id": "NCBI_ID", "match_mode": "hard"},
        {"display_id": "HGNC ID", "actual_id": "HGNC_ID", "match_mode": "hard"},
        {"display_id": "OMIM ID", "actual_id": "OMIM_ID", "match_mode": "hard"},
        {"display_id": "RefSeq ID", "actual_id": "RefSeq_ID", "match_mode": "hard"}
    ],
    "Transcript": [
        {"display_id": "Ensembl Gene ID", "actual_id": "Ensembl_Gene_ID", "match_mode": "hard"},
        {"display_id": "HGNC Symbol", "actual_id": "HGNC_Symbol", "match_mode": "hard"},
        {"display_id": "Ensembl Transcript ID", "actual_id": "Ensembl_Transcript_ID", "match_mode": "hard"},
        {"display_id": "Ensembl Transcript ID Version", "actual_id": "Ensembl_Transcript_ID_Version", "match_mode": "hard"},
        {"display_id": "RefSeq ID", "actual_id": "RefSeq_ID", "match_mode": "hard"},
        {"display_id": "RNACentral ID", "actual_id": "RNACentral_ID", "match_mode": "hard"}
    ],
    "Protein": [
        {"display_id": "HGNC Symbol", "actual_id": "HGNC_Symbol", "match_mode": "hard"},
        {"display_id": "Ensembl Protein ID", "actual_id": "Ensembl_Protein_ID", "match_mode": "hard"},
        {"display_id": "Ensembl Protein ID Version", "actual_id": "Ensembl_Protein_ID_Version", "match_mode": "hard"},
        {"display_id": "RefSeq ID", "actual_id": "RefSeq_ID", "match_mode": "hard"},
        {"display_id": "Uniprot ID", "actual_id": "Uniprot_ID", "match_mode": "hard"}
    ],
    "Promoter": [
        {"display_id": "HGNC Symbol", "actual_id": "HGNC_Symbol", "match_mode": "hard"},
        {"display_id": "Ensembl Gene ID", "actual_id": "Ensembl_Gene_ID", "match_mode": "hard"},
        {"display_id": "Ensembl Gene ID Version", "actual_id": "Ensembl_Gene_ID_Version", "match_mode": "hard"},
        {"display_id": "NCBI Gene ID", "actual_id": "NCBI_Gene_ID", "match_mode": "hard"},
        {"display_id": "HGNC ID", "actual_id": "HGNC_ID", "match_mode": "hard"},
        {"display_id": "OMIM ID", "actual_id": "OMIM_ID", "match_mode": "hard"},
        {"display_id": "RefSeq ID", "actual_id": "RefSeq_ID", "match_mode": "hard"}
    ],
    "Drug": [
        {"display_id": "Drug Name (Soft Match)", "actual_id": "Drug_Name", "match_mode": "soft"},
        {"display_id": "PubChem CID", "actual_id": "PubChem_CID", "match_mode": "hard"},
        {"display_id": "PubChem SID", "actual_id": "PubChem_SID", "match_mode": "hard"},
        {"display_id": "PubChem Name", "actual_id": "PubChem_Name", "match_mode": "hard"},
        {"display_id": "CAS RN", "actual_id": "CAS_RN", "match_mode": "hard"},
        {"display_id": "IUPAC Name", "actual_id": "IUPAC_Name", "match_mode": "hard"},
        {"display_id": "UNII", "actual_id": "UNII", "match_mode": "hard"},
        {"display_id": "UNII Name", "actual_id": "UNII_Name", "match_mode": "hard"},
        {"display_id": "NDC", "actual_id": "NDC", "match_mode": "hard"},
        {"display_id": "DrugBank ID", "actual_id": "DrugBank_ID", "match_mode": "hard"},
        {"display_id": "DrugBank Name", "actual_id": "DrugBank_Name", "match_mode": "hard"},
        {"display_id": "PubChem Canonical SMILES", "actual_id": "PubChem_Canonical_SMILES", "match_mode": "hard"},
        {"display_id": "UNII SMILES", "actual_id": "UNII_SMILES", "match_mode": "hard"},
        {"display_id": "InChI", "actual_id": "InChI", "match_mode": "hard"},
        {"display_id": "InChIKEY", "actual_id": "InChIKEY", "match_mode": "hard"},
        {"display_id": "PubChem Synonym", "actual_id": "PubChem_Synonym", "match_mode": "hard"}
    ],
    "Disease": [
        {"display_id": "Disease Name (Soft Match)", "actual_id": "Disease_Name", "match_mode": "soft"},
        {"display_id": "SNOMEDCT ID", "actual_id": "SNOMEDCT_ID", "match_mode": "hard"},
        {"display_id": "UMLS Name", "actual_id": "UMLS_Name", "match_mode": "hard"},
        {"display_id": "MeSH Name", "actual_id": "MeSH_Name", "match_mode": "hard"},
        {"display_id": "ICD11 ID", "actual_id": "ICD11_ID", "match_mode": "hard"},
        {"display_id": "ICD11 Title", "actual_id": "ICD11_Title", "match_mode": "hard"},
        {"display_id": "ICD10 ID", "actual_id": "ICD10_ID", "match_mode": "hard"},
        {"display_id": "DO ID", "actual_id": "DO_ID", "match_mode": "hard"},
        {"display_id": "DO Name", "actual_id": "DO_Name", "match_mode": "hard"},
        {"display_id": "UMLS ID", "actual_id": "UMLS_ID", "match_mode": "hard"},
        {"display_id": "MeSH ID", "actual_id": "MeSH_ID", "match_mode": "hard"},
        {"display_id": "OMIM ID", "actual_id": "OMIM_ID", "match_mode": "hard"},
        {"display_id": "MONDO ID", "actual_id": "MONDO_ID", "match_mode": "hard"},
        {"display_id": "MONDO Name", "actual_id": "MONDO_Name", "match_mode": "hard"},
        {"display_id": "SNOMEDCT Name", "actual_id": "SNOMEDCT_Name", "match_mode": "hard"}
    ],
    "Exposure": [
        {"display_id": "Exposure Name (Soft Match)", "actual_id": "Exposure_Name", "match_mode": "soft"},
        {"display_id": "MeSH ID", "actual_id": "MeSH_ID", "match_mode": "hard"},
        {"display_id": "CAS RN", "actual_id": "CAS_RN", "match_mode": "hard"}
    ],
    "Phenotype": [
        {"display_id": "Phenotype Name (Soft Match)", "actual_id": "Phenotype_Name", "match_mode": "soft"},
        {"display_id": "HPO ID", "actual_id": "HPO_ID", "match_mode": "hard"},
        {"display_id": "HPO Name", "actual_id": "HPO_Name", "match_mode": "hard"},
        {"display_id": "UMLS ID", "actual_id": "UMLS_ID", "match_mode": "hard"}
    ],
    "Pathway": [
        {"display_id": "PO ID", "actual_id": "PO_ID", "match_mode": "hard"},
        {"display_id": "PO Name", "actual_id": "PO_Name", "match_mode": "hard"},
        {"display_id": "KEGG Name", "actual_id": "KEGG_Name", "match_mode": "hard"},
        {"display_id": "Reactome Name", "actual_id": "Reactome_Name", "match_mode": "hard"},
        {"display_id": "Reactome ID", "actual_id": "Reactome_ID", "match_mode": "hard"},
        {"display_id": "WikiPathways Name", "actual_id": "WikiPathways_Name", "match_mode": "hard"},
        {"display_id": "WikiPathways ID", "actual_id": "WikiPathways_ID", "match_mode": "hard"},
        {"display_id": "KEGG ID", "actual_id": "KEGG_ID", "match_mode": "hard"}
    ],
    "Metabolite": [
        {"display_id": "HMDB ID", "actual_id": "HMDB_ID", "match_mode": "hard"},
        {"display_id": "PubChem CID", "actual_id": "PubChem_CID", "match_mode": "hard"},
        {"display_id": "CAS RN", "actual_id": "CAS_RN", "match_mode": "hard"},
        {"display_id": "ChemSpider ID", "actual_id": "ChemSpider_ID", "match_mode": "hard"},
        {"display_id": "PDB ID", "actual_id": "PDB_ID", "match_mode": "hard"},
        {"display_id": "ChEBI ID", "actual_id": "ChEBI_ID", "match_mode": "hard"},
        {"display_id": "KEGG ID", "actual_id": "KEGG_ID", "match_mode": "hard"},
        {"display_id": "HMDB Name", "actual_id": "HMDB_Name", "match_mode": "hard"},
        {"display_id": "ChEBI Name", "actual_id": "ChEBI_Name", "match_mode": "hard"},
        {"display_id": "IUPAC Name", "actual_id": "IUPAC_Name", "match_mode": "hard"},
        {"display_id": "SMILES", "actual_id": "SMILES", "match_mode": "hard"},
        {"display_id": "InChI", "actual_id": "InChI", "match_mode": "hard"},
        {"display_id": "InChIKey", "actual_id": "InChIKey", "match_mode": "hard"}
    ],
    "Microbiota": [
        {"display_id": "SILVA ID", "actual_id": "SILVA_ID", "match_mode": "hard"},
        {"display_id": "Greengenes ID", "actual_id": "Greengenes_ID", "match_mode": "hard"},
        {"display_id": "RDP ID", "actual_id": "RDP_ID", "match_mode": "hard"},
        {"display_id": "RNAcentral ID", "actual_id": "RNAcentral_ID", "match_mode": "hard"},
        {"display_id": "GTDB ID", "actual_id": "GTDB_ID", "match_mode": "hard"},
        {"display_id": "NCBI Taxonomy Name", "actual_id": "NCBI_Taxonomy_Name", "match_mode": "hard"},
        {"display_id": "NCBI Taxonomy ID", "actual_id": "NCBI_Taxonomy_ID", "match_mode": "hard"}
    ]

}
DEFAULT_ENTITY_ORDER = ["Promoter", "Gene", "Transcript", "Protein", "Pathway", "Metabolite", "Microbiota", "Exposure","Phenotype", "Disease", "Drug"]

# Define entity types and their colors
ENTITY_TYPES_COLORS = {
    "Promoter": "#ed7d31",
    "Gene": "#f59393",
    "Transcript": "#64cbf0",
    "Protein": "#ffcd33",
    "Pathway": "#91cf50",
    "Exposure": "#836599",
    "Metabolite": "#f9cb9c",
    "Drug": "#b5b5b5",
    "Microbiota": "#87a771",
    "Phenotype": "#62a3d1",
    "Disease": "#b58a6d"
}

# Fixed node positions
NODE_POSITIONS = {
    "Promoter": (-330, -20),
    "Gene": (-200, -50),
    "Transcript": (-100, 0),
    "Protein": (-50, 100),
    "Pathway": (-20, -30),
    "Exposure": (50, -170),
    "Metabolite": (80, 150),
    "Drug": (200, -120),
    "Microbiota": (250, 200),
    "Phenotype": (300, -50),
    "Disease": (350, 80),


}

# Define relationships (directed edges)
EDGES = [
    # Core relationships
    ("Promoter", "Gene"),
    ("Gene", "Transcript"),
    ("Transcript", "Protein"),

    # Protein relationships (4)
    ("Protein", "Protein"),
    ("Protein", "Pathway"),
    ("Protein", "Disease"),
    ("Protein", "Phenotype"),

    # Pathway relationships (2)
    ("Pathway", "Drug"),
    ("Pathway", "Protein"),

    # Exposure relationships (3)
    ("Exposure", "Gene"),
    ("Exposure", "Pathway"),
    ("Exposure", "Disease"),

    # Microbiota relationships (3)
    ("Metabolite", "Metabolite"),
    ("Metabolite", "Protein"),
    ("Metabolite", "Disease"),

    # Drug relationships (7)
    ("Drug", "Drug"),
    ("Drug", "Pathway"),
    ("Drug", "Protein"),
    ("Drug", "Metabolite"),
    ("Drug", "Microbiota"),
    ("Drug", "Disease"),
    ("Drug", "Phenotype"),

    # Microbiota relationships (1)
    ("Microbiota", "Disease"),

    # Disease relationships (2)
    ("Disease", "Disease"),
    ("Disease", "Phenotype"),

    # Phenotype relationships (2)
    ("Phenotype", "Phenotype"),
    ("Phenotype", "Disease"),

]

# --------------------------- HELPER FUNCTIONS -----------------------------------

def get_display_ids_for_entity(entity_type: str) -> List[str]:
    if entity_type not in ID_TYPES:
        return []
    return [item["display_id"] for item in ID_TYPES[entity_type]]

def get_id_info_from_display(entity_type: str, display_id: str) -> Dict[str, str]:
    if entity_type not in ID_TYPES:
        return {"actual_id": "", "match_mode": "hard"}
    for item in ID_TYPES[entity_type]:
        if item["display_id"] == display_id:
            return {"actual_id": item["actual_id"], "match_mode": item["match_mode"]}
    return {"actual_id": "", "match_mode": "hard"}

