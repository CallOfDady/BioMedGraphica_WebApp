# frontend/components/usage_notes.py
import streamlit as st

def render_usage_notes():
    """
    Render usage notes panel explaining how to use the BiomedGraphica Integration App.
    """

    st.subheader("🧭 Usage Notes")

    st.markdown("""
    1. **Prepare Data or [Download Example Data (TCGA-BRCA)](https://drive.usercontent.google.com/download?id=1O-5bRrOb1Yf7v1Jy8YpsmP6ltDUglFps&export=download)**
       
       - Before starting, ensure you have the necessary feature files (multi-omics datasets) and a sample label file.
       - To quickly explore the workflow or to use as a reference for data preparation, you can refer to the provided **TCGA-BRCA example dataset** (30 MB).
    """)

    st.markdown("""
    2. **Data Preparation: Entities & Labels**
       
       - Each feature file should have sample IDs in the **first column**, harmonized across all files.  
       - Feature columns should use **standardized identifiers** (e.g., Ensembl, HGNC) or clearly defined names (e.g., drug names, HPO terms).  
       - During upload, the system analyzes **graph connectivity** and suggests **missing virtual entities** if needed.
    """)

    st.markdown("""
    3. **Configuration & Integration**
       
       - In **Step 2**, the system automatically orders entities following biological signaling flow.  
       - Users can manually refine this order via the **interactive reordering panel**.  
       - You may enable **Z-score normalization** and select **edge (relation) types** to include.
    """)

    st.markdown("""
    4. **Processing & Results**
       
       - Once configuration is finalized, the pipeline performs **identifier alignment**, **hard/soft matching**, and **graph construction**.  
       - Soft matches trigger an **interactive confirmation** step for human-in-the-loop verification.  
       - The resulting **graph-structured data** and **entity mappings** are packaged for **direct AI model input** and can be downloaded from the results panel.
    """)

    st.info("💡 *For more details, please check our GitHub page: [BioMedGraphica](https://github.com/FuhaiLiAiLab/BioMedGraphica). Questions or feedback are welcome via GitHub issues.*")
