# components/entity_row.py

import streamlit as st
import os
import streamlit_nested_layout
from biomedgraphica_app_constants import ENTITY_TYPES, ID_TYPES

def match_entity_type(filename: str) -> str | None:

    name_lower = filename.lower()

    # 1. keyword-based matching
    keyword_map = {
        "promoter": "Promoter",
        "gene": "Gene",
        "protein": "Protein",
        "disease": "Disease",
        "drug": "Drug",
        "microbiota": "Microbiota",
        "pathway": "Pathway",
        "phenotype": "Phenotype",
        "exposure": "Exposure",
        "metabolite": "Metabolite",
        "transcript": "Transcript"
    }

    for keyword, entity in keyword_map.items():
        if keyword in name_lower:
            return entity

    # 2. fallback: if entity name is included, return it directly
    for entity in ENTITY_TYPES:
        if entity.lower() in name_lower:
            return entity

    return None

def log_to_console(message: str):
    logs = st.session_state.get("log_messages", [])
    logs.append(message)
    st.session_state["log_messages"] = logs

def render_entity_row(ent: dict) -> bool:
    """Render one entity row and return True if marked for removal."""
    remove = False

    col_del, col_form, col_upload = st.columns([0.5, 6, 4], gap="medium")

    # ---------- Delete Button ----------
    with col_del:
        st.markdown("<div style='height: 2.0em'></div>", unsafe_allow_html=True)  # Add vertical space for alignment
        if st.button("✖", key=f"rm_{ent['uuid']}"):
            remove = True

    # ---------- Form Column ----------
    with col_form:
        # Upper Row:  Fill0 + Label (Equal Width)
        upper = st.columns([1, 1])
        with upper[0]:
            node_type_options = ["Real Node", "Virtual Node"]
            selected = st.selectbox("Node Type", node_type_options,
                                    index=1 if ent.get("fill0") else 0,
                                    key=f"ntype_{ent['uuid']}")

            ent["fill0"] = selected == "Virtual Node"
            if ent["fill0"]:
                ent["file_path"] = ""
        with upper[1]:
            ent["feature_label"] = st.text_input("Label", value=ent["feature_label"], key=f"lab_{ent['uuid']}")

        # Lower Row: Type / ID (Equal Width)
        lower = st.columns([1, 1])
        with lower[0]:
            display_index = ENTITY_TYPES.index(ent["entity_type"]) if ent["entity_type"] in ENTITY_TYPES else 0
            ent["entity_type"] = st.selectbox("Entity Type", ENTITY_TYPES, index=display_index, key=f"typ_{ent['uuid']}")
        with lower[1]:
            opts = ID_TYPES.get(ent["entity_type"], [""])
            display_id_index = opts.index(ent["id_type"]) if ent["id_type"] in opts else 0
            ent["id_type"] = st.selectbox("ID Type", opts, index=display_id_index, key=f"idt_{ent['uuid']}")

    # ---------- Upload Column ----------

    with col_upload:
        st.markdown("Upload", help="Upload .csv/.tsv/.txt file")

        if ent["fill0"]:
            st.text_input("Upload", "", placeholder=" ", disabled=True, key=f"upl_dis_{ent['uuid']}")
        else:
            upf = st.file_uploader("Upload", type=["csv", "tsv", "txt"], key=f"upl_{ent['uuid']}", label_visibility="collapsed")
            if upf is not None:
                # Check if the file has been uploaded before
                if ent.get("_uploaded_once") and ent.get("file_path") == upf.name:
                    return remove  # exit early if already uploaded

                ent["file_path"] = upf.name
                ent["_uploaded_once"] = True  # Set uploaded flag

                log_to_console(f"📁 File uploaded: `{upf.name}`")

                updated = False

                # Label auto-fill
                if not ent["feature_label"].strip() and not ent.get("auto_fill_label"):
                    filename_base = os.path.splitext(upf.name)[0]
                    ent["feature_label"] = filename_base
                    ent["auto_fill_label"] = True
                    log_to_console(f"✅ Auto-filled label from file: `{filename_base}`")
                    updated = True
                elif ent.get("auto_fill_label"):
                    pass
                else:
                    log_to_console("⚠️ Label already filled. Skipped auto-fill.")

                # Entity type auto-detect
                if not ent["entity_type"] and not ent.get("auto_fill_type"):
                    matched = match_entity_type(upf.name)
                    if matched:
                        ent["entity_type"] = matched
                        ent["auto_fill_type"] = True
                        log_to_console(f"✅ Auto-detected entity type: `{matched}`")
                        updated = True
                    else:
                        log_to_console("⚠️ No matching entity type found in filename.")
                elif ent.get("auto_fill_type"):
                    pass
                else:
                    log_to_console("⚠️ Entity type already selected. Skipped auto-detect.")

                if updated:
                    st.rerun()

    st.markdown("<hr style='margin-top: 0.5rem; margin-bottom: 0.8rem;'>", unsafe_allow_html=True)
    return remove


