# components/entity_row.py

import streamlit as st
import os
import streamlit_nested_layout
from biomedgraphica_app_constants import ENTITY_TYPES, ID_TYPES
from .knowledge_graph import ENTITY_TYPES_COLORS

def match_entity_type(filename: str) -> str | None:
    name_lower = filename.lower()
    keyword_map = {
        "promoter": "Promoter", "gene": "Gene", "protein": "Protein", "disease": "Disease",
        "drug": "Drug", "microbiota": "Microbiota", "pathway": "Pathway", "phenotype": "Phenotype",
        "exposure": "Exposure", "metabolite": "Metabolite", "transcript": "Transcript"
    }
    for keyword, entity in keyword_map.items():
        if keyword in name_lower:
            return entity
    for entity in ENTITY_TYPES:
        if entity.lower() in name_lower:
            return entity
    return None

def log_to_console(message: str):
    logs = st.session_state.get("log_messages", [])
    logs.append(message)
    st.session_state["log_messages"] = logs


# ---------- BINDING HELPERS ----------

def bind_input(label: str, key: str, ent: dict, field: str, help: str | None = None):
    value = ent.get(field, "")
    new_value = st.text_input(label, value=value, key=key, help=help)
    ent[field] = new_value
    return new_value


def bind_selectbox(label: str, options: list[str], key: str, ent: dict, field: str, disabled=False, fallback=None, help: str | None = None):
    # Get the current value from session state first, then from entity dict
    current_value = st.session_state.get(key)
    if current_value is None:
        current_value = ent.get(field, fallback or options[0])
    
    # Ensure the value is in options
    if current_value not in options:
        current_value = options[0] if options else ""
    
    # Find the index
    try:
        index = options.index(current_value)
    except ValueError:
        index = 0
        current_value = options[0] if options else ""
    
    # Create the selectbox
    new_value = st.selectbox(label, options, index=index, key=key, disabled=disabled, help=help)

    # Update the entity dict with the new value
    ent[field] = new_value
    
    return new_value


# ---------- MAIN RENDER FUNCTION ----------

def render_entity_row(ent: dict) -> bool:
    uuid = ent["uuid"]
    remove = False

    col_del, col_color, col_form, col_upload = st.columns([0.5, 0.3, 6, 4], gap="medium")

    # ---------- Delete Button ----------
    with col_del:
        st.markdown("<div style='height: 2.0em'></div>", unsafe_allow_html=True)
        if st.button("✖", key=f"rm_{uuid}"):
            return True

    # ---------- Color Box ----------
    with col_color:
        # Get the current entity type from session state first, then from entity dict
        entity_type_key = f"typ_{uuid}"
        current_entity_type = st.session_state.get(entity_type_key)
        if current_entity_type is None:
            current_entity_type = ent.get("entity_type", "")
        
        color = ENTITY_TYPES_COLORS.get(current_entity_type, "transparent")
        st.markdown("<div style='height: 0.5em'></div>", unsafe_allow_html=True) # Add some space
        st.markdown(
            f"<div style='width: 100%; height: 8.5em; border-radius: 0.4rem; background-color: {color}; border: 1px solid #ccc;'></div>",
            unsafe_allow_html=True
        )

    # ---------- Form Column ----------
    with col_form:
        upper = st.columns([1, 1])

        # Node Type
        with upper[0]:
            # Convert boolean fill0 to string for selectbox
            current_node_type = "Virtual Node" if ent.get("fill0", False) else "Real Node"
            
            node_type = st.selectbox(
                label="Node Type",
                options=["Real Node", "Virtual Node"],
                index=0 if current_node_type == "Real Node" else 1,
                key=f"ntype_{uuid}",
                help="Select the type of node for this entity."
            )
            
            # Update the fill0 field based on node type
            is_virtual = node_type == "Virtual Node"
            ent["fill0"] = is_virtual
            
            # Clear file path and id_type when switching to virtual node
            if is_virtual:
                ent["file_path"] = ""
                ent["id_type"] = ""

        # Label
        with upper[1]:
            bind_input("Label", key=f"lab_{uuid}", ent=ent, field="feature_label", help="Enter a label for this entity.")

        lower = st.columns([1, 1])

        # Entity Type
        with lower[0]:
            bind_selectbox(
                label="Entity Type",
                options=ENTITY_TYPES,
                key=f"typ_{uuid}",
                ent=ent,
                field="entity_type",
                help="Select the type of entity."
            )

        # ID Type
        with lower[1]:
            if ent.get("fill0"):
                st.selectbox("ID Type", ["(N/A for virtual)"], disabled=True, key=f"idt_{uuid}_disabled")
            else:
                entity_type = ent.get("entity_type", "")
                opts = ID_TYPES.get(entity_type, [""])
                
                # If entity type changed, reset ID type to first option
                current_id_type = ent.get("id_type", "")
                if current_id_type not in opts:
                    ent["id_type"] = opts[0] if opts else ""
                
                bind_selectbox(
                    label="ID Type",
                    options=opts,
                    key=f"idt_{uuid}",
                    ent=ent,
                    field="id_type",
                    help="Select the ID type for this entity."
                )

    # ---------- Upload ----------
    with col_upload:
        st.markdown("Upload", help="Upload .csv/.tsv/.txt file")
        if ent.get("fill0"):
            st.text_input("Upload", "", placeholder=" ", disabled=True, key=f"upl_dis_{uuid}")
        else:
            upf = st.file_uploader("Upload", type=["csv", "tsv", "txt"],
                                   key=f"upl_{uuid}", label_visibility="collapsed")
            if upf is not None:
                if ent.get("_uploaded_once") and ent.get("file_path") == upf.name:
                    return False

                ent["file_path"] = upf.name
                ent["_uploaded_once"] = True
                log_to_console(f"📁 File uploaded: `{upf.name}`")

                updated = False

                # Auto-fill label
                if not ent["feature_label"].strip() and not ent.get("auto_fill_label"):
                    base = os.path.splitext(upf.name)[0]
                    ent["feature_label"] = base
                    ent["auto_fill_label"] = True
                    log_to_console(f"✅ Auto-filled label from file: `{base}`")
                    updated = True
                elif ent.get("auto_fill_label"):
                    pass
                else:
                    log_to_console("⚠️ Label already filled. Skipped auto-fill.")

                # Auto-detect entity type
                if not ent.get("entity_type") and not ent.get("auto_fill_type"):
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
    return False