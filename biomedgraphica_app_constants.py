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
DEFAULT_ENTITY_ORDER = ["Promoter", "Gene", "Transcript", "Protein"]

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

