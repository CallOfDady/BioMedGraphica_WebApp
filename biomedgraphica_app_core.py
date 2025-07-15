"""
biomedgraphica_core.py

"""

import json, uuid, os
from typing import Dict, List

from biomedgraphica_app_constants import (
    ENTITY_TYPES, ID_TYPES, DEFAULT_ENTITY_ORDER
)
from components.entity_row import render_entity_row, validate_entities, check_label_file, analyze_knowledge_graph_connectivity, generate_edge_types_from_entities
from components.log_console import render_log_console, log_to_console
from components.knowledge_graph import render_knowledge_graph
from components.job_status_panel import render_job_status_panel
from utils.temp_manager import get_temp_manager
from utils.app_init import initialize_app

import streamlit as st
from streamlit_sortables import sort_items


# --------------------------- HELPERS -------------------------------------

def _generate_default_entity_order(entities):
    """
    Generate default entity order based on entity types and labels.
    Uses DEFAULT_ENTITY_ORDER for priority, with labels as display names.
    """
    
    # Create a mapping from entity type to its priority order
    entity_type_priority = {}
    for i, entity_type in enumerate(DEFAULT_ENTITY_ORDER):
        entity_type_priority[entity_type] = i
    
    # Create list of tuples (priority, label) for sorting
    entity_list = []
    for e in entities:
        label = e["feature_label"].strip()
        if label:
            entity_type = e.get("entity_type", "")
            # Use priority from DEFAULT_ENTITY_ORDER, or assign high number for unknown types
            priority = entity_type_priority.get(entity_type, 999)
            entity_list.append((priority, label))
    
    # Sort by priority and return labels
    entity_list.sort(key=lambda x: x[0])
    return [label for _, label in entity_list]

def _build_file_order(entities):
    return _generate_default_entity_order(entities)

def log_to_console(message: str):
    logs = st.session_state.get("log_messages", [])
    logs.append(message)
    st.session_state["log_messages"] = logs

# --------------------------- MAIN BUILDER --------------------------------

def build_app():

    # ---------- App Initialization ----------
    initialize_app()

    # ---------- Session init ----------
    if "entities" not in st.session_state:
        st.session_state.entities = [dict(uuid=str(uuid.uuid4()), fill0=False, feature_label="", entity_type="", id_type=ID_TYPES[""][0], file_path="") for _ in range(2)]
    st.session_state.setdefault("label_path", "")
    st.session_state.setdefault("file_order", [])
    st.session_state.setdefault("edge_types", [])
    st.session_state.setdefault("selected_edge_types", [])
    st.session_state.setdefault("apply_zscore", False)
    st.session_state.setdefault("step1_open", True)
    st.session_state.setdefault("step2_open", False)

    st.session_state.setdefault("log_messages", ["📟 Processing console initialized."])

    # ---------- UI ----------
    st.set_page_config(f"BiomedGraphica Integration", layout="wide")
    st.title("🧬 BiomedGraphica – Data Integration")

    # ---------- Project Header ----------
    st.markdown("""
    **BioMedGraphica Data Integration App** is a Web-based GUI tool that enables researchers to convert biomedical data into structured graph-ready format for **AI in Precision Health and Medicine**.

    - Upload and align **multi-omics and clinical datasets**
    - Perform **entity recognition** via hard or soft matching
    - Construct **custom knowledge-signaling graphs**
    - Export **graph-ready `.npy` files** for downstream modeling
    """)

    # ---------- Job Status Panel ----------
    temp_manager = get_temp_manager()
    render_job_status_panel(temp_manager)


    st.divider()

    # Two main columns for the app
    main_left, main_right = st.columns([3, 2], gap="large")

    with main_left:

        # -------- Step 1 --------
        with st.expander("Step 1 – Entities & Labels", expanded=st.session_state.step1_open):
            st.subheader("Entities")

            # Entity rows (import from components/entity_row.py)
            remove_indices = []
            for i, ent in enumerate(st.session_state.entities):
                if render_entity_row(ent):
                    remove_indices.append(i)

            # Remove selected rows
            for i in sorted(remove_indices, reverse=True):
                del st.session_state.entities[i]
            if remove_indices:
                st.rerun()

            # Add entity buttons
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
            
            with btn_col1:
                if st.button("➕ Add Entity", use_container_width=True):
                    st.session_state.entities.append(dict(
                        uuid=str(uuid.uuid4()),
                        fill0=False,
                        feature_label="",
                        entity_type="",
                        id_type=ID_TYPES[""][0],
                        file_path=""
                    ))
                    st.rerun()
            
            with btn_col2:
                if st.button("🔧 Add Missing Entities", use_container_width=True):
                    # Analyze connectivity and add missing nodes
                    connectivity_analysis = analyze_knowledge_graph_connectivity(st.session_state.entities)
                    missing_nodes = connectivity_analysis.get("missing_nodes", [])
                    
                    if missing_nodes:
                        for missing_node in missing_nodes:
                            st.session_state.entities.append(dict(
                                uuid=str(uuid.uuid4()),
                                fill0=True,  # Virtual node
                                feature_label=missing_node.lower(),
                                entity_type=missing_node,
                                id_type="",
                                file_path=""
                            ))
                        log_to_console(f"🔧 Added missing virtual nodes: {', '.join(missing_nodes)}")
                        st.rerun()
                    else:
                        st.info("No missing nodes needed for connectivity")
            
            with btn_col3:
                if st.button("🔗 Add All Entities", use_container_width=True):
                    # Get currently selected entity types
                    selected_types = set()
                    for ent in st.session_state.entities:
                        if ent.get("entity_type", "").strip():
                            selected_types.add(ent.get("entity_type"))
                    
                    # Add all missing entity types as virtual nodes
                    all_entity_types = [et for et in ENTITY_TYPES if et.strip()]  # Remove empty string
                    missing_entity_types = [et for et in all_entity_types if et not in selected_types]
                    
                    if missing_entity_types:
                        for entity_type in missing_entity_types:
                            st.session_state.entities.append(dict(
                                uuid=str(uuid.uuid4()),
                                fill0=True,  # Virtual node
                                feature_label=entity_type.lower(),
                                entity_type=entity_type,
                                id_type="",
                                file_path=""
                            ))
                        log_to_console(f"🔗 Added all supporting entities as virtual nodes to construct the full connectivity graph: {', '.join(missing_entity_types)}")
                        st.rerun()
                    else:
                        st.info("All entity types are already present")

            st.markdown("---")

            # Label file upload
            st.subheader("Label")
            
            # Label file upload with automatic cleanup when uploader is cleared
            lup = st.file_uploader("Upload Label File", type=["csv", "tsv", "txt"], key="lbl_up", label_visibility="collapsed")
            
            # Get temp manager and handle label file upload changes
            temp_manager = get_temp_manager()
            previous_file_key = "_had_label_file"
            previous_filename_key = "_label_filename"
            saved_label_path = temp_manager.handle_label_file_change(lup, previous_file_key, previous_filename_key)
            
            if saved_label_path:
                # Label file was uploaded
                # Check if this is a new upload
                if st.session_state.get("_label_file_path") != saved_label_path:
                    st.session_state.label_path = saved_label_path
                    st.session_state["_label_file_path"] = saved_label_path
                    st.session_state["_label_uploaded_once"] = True
                    log_to_console(f"🏷️ Label file saved: `{lup.name}` → `{saved_label_path}`")
            else:
                # Label file was cleared (automatic cleanup was already handled)
                # Just update the session state
                if st.session_state.get("_label_uploaded_once"):
                    st.session_state.label_path = ""
                    st.session_state["_label_file_path"] = ""
                    st.session_state["_label_uploaded_once"] = False
                    log_to_console(f"🗑️ Label file cleared")
                    st.rerun()

            # Next button
            btn_l, btn_r = st.columns([1, 1])
            with btn_l:
                st.empty()
            with btn_r:
                if st.button("Next ➡", key="step1_next", use_container_width=True):
                    # Validate entities
                    entity_validation = validate_entities(st.session_state.entities)
                    label_validation = check_label_file(st.session_state.label_path)
                    
                    # check connectivity of the knowledge graph
                    connectivity_analysis = analyze_knowledge_graph_connectivity(st.session_state.entities)
                    
                    # gather all errors
                    all_errors = []
                    all_errors.extend(entity_validation["errors"])
                    all_errors.extend(label_validation["errors"])
                    
                    if all_errors:
                        # Display error messages
                        for error in all_errors:
                            st.error(f"❌ {error}")
                        st.stop()
                    
                    # check connectivity
                    if not connectivity_analysis["connected"]:
                        if connectivity_analysis["missing_nodes"]:
                            st.warning("⚠️ **Knowledge Graph Connectivity Issues:**")
                            for suggestion in connectivity_analysis["suggestions"]:
                                st.warning(f"• {suggestion}")
                            
                            # auto-add missing virtual nodes
                            if st.button("🔧 Auto-add missing virtual nodes", key="auto_add_virtual"):
                                import uuid as uuid_module
                                for missing_node in connectivity_analysis["missing_nodes"]:
                                    st.session_state.entities.append(dict(
                                        uuid=str(uuid_module.uuid4()),
                                        fill0=True,  # Virtual node
                                        feature_label=missing_node.lower(),  # Use lowercase label
                                        entity_type=missing_node,
                                        id_type="",
                                        file_path=""
                                    ))
                                log_to_console(f"🔧 Auto-added virtual nodes: {', '.join(connectivity_analysis['missing_nodes'])}")
                                st.rerun()
                        
                        if connectivity_analysis["broken_paths"]:
                            st.error("❌ **Disconnected paths found:**")
                            for source, target in connectivity_analysis["broken_paths"]:
                                st.error(f"• No path between {source} and {target}")
                    
                    # if entity_validation["valid"] and label_validation["valid"]:
                    if entity_validation["valid"] and label_validation["valid"]:
                        # generate edge types
                        generated_edge_types = generate_edge_types_from_entities(st.session_state.entities)
                        st.session_state.edge_types = generated_edge_types
                        st.session_state.selected_edge_types = generated_edge_types.copy()  # Default select all
                        
                        st.session_state.file_order = _build_file_order(st.session_state.entities)
                        st.session_state.step1_open, st.session_state.step2_open = False, True
                        log_to_console("✅ Validation passed. Proceeding to Step 2.")
                        st.rerun()

        # -------- Step 2 --------
        with st.expander("Step 2 – Finalise & Run", expanded=st.session_state.step2_open):
            l, r = st.columns(2)
            with l:
                st.subheader("Entity Order")
                
                # Get current file order from session state
                current_file_order = st.session_state.get("file_order", [])
                
                if current_file_order:
                    # Use streamlit-sortables for manual reordering
                    # Create a unique key that includes the order content to force refresh
                    sortable_key = f"entity_order_sortable_{len(current_file_order)}_{hash(tuple(current_file_order))}"
                    st.write("Drag to reorder entities (left to right order):")
                    sorted_items = sort_items(current_file_order, key=sortable_key)
                    
                    # Update session state with new order
                    st.session_state.file_order = sorted_items
                else:
                    st.info("Entity order will be generated automatically when you proceed from Step 1.")

                # Z-score normalization checkbox
                st.checkbox("Apply Z-score", key="zscore_check")
                z_before = st.session_state.get("_last_zscore_val", None)
                z_now = st.session_state["zscore_check"]
                if z_before is not None and z_before != z_now:
                    status = "enabled" if z_now else "disabled"
                    log_to_console(f"⚙️ Z-score normalization {status}.")
                st.session_state["_last_zscore_val"] = z_now
                st.session_state.apply_zscore = z_now  # store in session state

            with r:
                st.subheader("Edge Types")
                
                # Get available edge types from session state
                available_edge_types = st.session_state.get("edge_types", [])
                
                if available_edge_types:
                    # Get current selection from session state
                    if "edge_multiselect" in st.session_state:
                        current_selection = st.session_state["edge_multiselect"]
                    else:
                        current_selection = st.session_state.get("selected_edge_types", available_edge_types)
                    
                    # Multiselect for edge types
                    selected_edges = st.multiselect(
                        "Choose edge types:",
                        options=available_edge_types,
                        default=current_selection,
                        key="edge_multiselect"
                    )

                    # Select All / Select None buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Select All", key="select_all_edges", use_container_width=True):
                            st.session_state.selected_edge_types = available_edge_types.copy()
                            # Remove multiselect's session state to force reload
                            if "edge_multiselect" in st.session_state:
                                del st.session_state["edge_multiselect"]
                            st.rerun()
                    with col2:
                        if st.button("Select None", key="select_none_edges", use_container_width=True):
                            st.session_state.selected_edge_types = []
                            # Remove multiselect's session state to force reload
                            if "edge_multiselect" in st.session_state:
                                del st.session_state["edge_multiselect"]
                            st.rerun()
                    
                    # Update session state
                    st.session_state.selected_edge_types = selected_edges
                else:
                    st.info("Edge types will be generated automatically when you proceed from Step 1.")
                    
            db = st.text_input("DB path", "E:/LabWork/BioMedGraphica-Conn")
            od = st.text_input("Output dir", "cache")

            # Back and Run buttons
            btn_l, btn_r = st.columns([1, 1])
            with btn_l:
                if st.button("⬅ Back", key="step2_back", use_container_width=True):
                    st.session_state.step1_open, st.session_state.step2_open = True, False
                    st.rerun()
            with btn_r:
                if st.button("▶️ Run processing", key="step2_run", use_container_width=True):
                    cfgs = [
                        dict(
                            feature_label=e["feature_label"],
                            entity_type=e["entity_type"].lower(),
                            id_type=e["id_type"],
                            file_path=e["file_path"],
                            fill0=e["fill0"]
                        )
                        for e in st.session_state.entities if e["feature_label"].strip()
                    ]
                    if st.session_state.label_path:
                        cfgs.append(dict(
                            feature_label="label",
                            entity_type="label",
                            id_type="",
                            file_path=st.session_state.label_path,
                            fill0=False
                        ))
                    final = dict(
                        configs=cfgs,
                        finalize=dict(
                            file_order=st.session_state.file_order,
                            apply_zscore=st.session_state.apply_zscore,
                            edge_types=st.session_state.selected_edge_types,
                        )
                    )
                    st.code(json.dumps(final, indent=2), language="json")
                    try:
                        from backend.processors import process
                        res = process(
                            *final["configs"],
                            database_path=db,
                            output_dir=od,
                            file_order=final["finalize"].get("file_order"),
                            apply_zscore=final["finalize"].get("apply_zscore", False),
                            edge_types=final["finalize"].get("edge_types")
                        )
                        st.success(f"Done: {res['summary']['success']} / {res['summary']['total']}")
                        log_to_console("✅ Processing completed successfully.")
                    except Exception as exc:
                        st.exception(exc)
                        log_to_console(f"❌ Error during processing: {exc}")

    with main_right:
        # Graph
        render_knowledge_graph()

        st.divider()

        # Status info box
        render_log_console()

    # # ---------- style tweaks ----------

    # </style>""", unsafe_allow_html=True)