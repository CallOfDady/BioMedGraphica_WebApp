"""
biomedgraphica_core.py

"""

import json, uuid, os
from typing import Dict, List

from frontend.constants import (
    ENTITY_TYPES, ID_TYPES, DEFAULT_ENTITY_ORDER,
    get_display_ids_for_entity, get_id_info_from_display
)

from frontend.utils.job_manager import get_job_manager
from frontend.init_job_manager import initialize_job_manager

from frontend.components.job_status_panel import render_job_status_panel

from frontend.components.entity_row import render_entity_row, validate_entities, check_label_file, analyze_knowledge_graph_connectivity, generate_edge_types_from_entities
from frontend.components.log_console import render_log_console, log_to_console
from frontend.components.knowledge_graph import render_knowledge_graph

from frontend.components.mapping_selector import render_mapping_selector

from frontend.api.client import submit_async_processing_task, submit_mappings_to_backend, check_task_status

import streamlit as st
import streamlit_nested_layout
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
    # ---------- App Initialization ----------
    # Init job manager
    job_manager, job_id, job_data_output_dir = initialize_job_manager()

    # ---------- Session init ----------
    if "entities" not in st.session_state:
        st.session_state.entities = [dict(uuid=str(uuid.uuid4()), fill0=False, feature_label="", entity_type="", id_type=get_display_ids_for_entity("")[0], file_path="") for _ in range(2)]
    st.session_state.setdefault("label_path", "")
    st.session_state.setdefault("file_order", [])
    st.session_state.setdefault("edge_types", [])
    st.session_state.setdefault("selected_edge_types", [])
    st.session_state.setdefault("apply_zscore", False)
    st.session_state.setdefault("step1_open", True)
    st.session_state.setdefault("step2_open", False)

    st.session_state.setdefault("log_messages", ["📟 Processing console initialized."])

    # ---------- Job Status Panel ----------
    render_job_status_panel(job_manager)

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
                if render_entity_row(ent, job_manager):
                    remove_indices.append(i)

            # Remove selected rows
            for i in sorted(remove_indices, reverse=True):
                del st.session_state.entities[i]
            if remove_indices:
                # Update file order to reflect entity removal
                current_entities = [ent["feature_label"] for ent in st.session_state.entities]
                current_file_order = st.session_state.get("file_order", [])
                # Keep only entities that still exist
                updated_file_order = [label for label in current_file_order if label in current_entities]
                st.session_state.file_order = updated_file_order
                log_to_console(f"📋 Entity order updated after removal: {' → '.join(updated_file_order)}")
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
                        id_type=get_display_ids_for_entity("")[0],
                        file_path=""
                    ))
                    log_to_console("📋 Added new entity row")
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
            
            # handle label file upload changes
            previous_file_key = "_had_label_file"
            previous_filename_key = "_label_filename"
            saved_label_path = job_manager.handle_label_file_change(lup, previous_file_key, previous_filename_key)

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
                        # Generate file order (edge types are generated dynamically in Step 2)
                        st.session_state.file_order = _build_file_order(st.session_state.entities)
                        st.session_state.step1_open, st.session_state.step2_open = False, True
                        log_to_console("✅ Validation passed. Proceeding to Step 2.")
                        st.rerun()

        # -------- Step 2 --------
        with st.expander("Step 2 – Finalise & Run", expanded=st.session_state.step2_open):
            l, r = st.columns(2)
            with l:
                st.markdown("#### Entity Order")

                # Get current file order from session state
                current_file_order = st.session_state.get("file_order", [])
                
                # Get current entities to ensure file_order is in sync
                current_entities = [ent["feature_label"] for ent in st.session_state.entities if ent.get("feature_label", "").strip()]
                
                # Update file_order if entities have changed
                if set(current_file_order) != set(current_entities):
                    # Keep existing order where possible, append new ones
                    updated_order = [label for label in current_file_order if label in current_entities]
                    new_entities = [label for label in current_entities if label not in updated_order]
                    updated_order.extend(new_entities)
                    st.session_state.file_order = updated_order
                    current_file_order = updated_order
                    # log_to_console(f"Entity order synced: {' → '.join(updated_order)}")

                if current_file_order:
                    st.markdown(
                        "<span style='font-size:14px;'>Drag to reorder entities.</span>",
                        unsafe_allow_html=True
                    )
                    # Use dynamic key based on entity count and names to force refresh when entities change
                    entity_hash = hash(tuple(current_file_order))
                    sortable_key = f"entity_order_sortable_{entity_hash}"
                    
                    # Use streamlit-sortables for manual reordering
                    sorted_items = sort_items(current_file_order, key=sortable_key)
                    
                    # Check if the order has changed and update immediately
                    if sorted_items != current_file_order:
                        st.session_state.file_order = sorted_items
                        log_to_console(f"📋 Entity order updated: {' → '.join(sorted_items)}")
                        st.rerun()
                    
                    # Display current order
                    st.caption(f"Current order:\n{' → '.join(current_file_order)}")
                else:
                    st.info("Entity order will be generated automatically based on your selected entities.")

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
                st.markdown("#### Edge Types")
                
                # Generate edge types dynamically based on current entities
                current_edge_types = generate_edge_types_from_entities(st.session_state.entities)
                
                # Update session state if edge types have changed
                if current_edge_types != st.session_state.get("edge_types", []):
                    st.session_state.edge_types = current_edge_types
                    # Update selected edge types to include new ones by default
                    current_selected = st.session_state.get("selected_edge_types", [])
                    # Keep existing selections that are still valid, add new ones
                    updated_selected = [et for et in current_selected if et in current_edge_types]
                    new_edge_types = [et for et in current_edge_types if et not in updated_selected]
                    updated_selected.extend(new_edge_types)
                    st.session_state.selected_edge_types = updated_selected
                    
                    # Get current entity types for logging
                    current_entities = [ent.get("entity_type", "") for ent in st.session_state.entities if ent.get("entity_type", "").strip()]
                    # log_to_console(f" Edge types updated based on entities {current_entities}: {', '.join(current_edge_types)}")
                
                available_edge_types = current_edge_types
                
                if available_edge_types:
                    # Get current selection from session state
                    current_selection = st.session_state.get("selected_edge_types", available_edge_types)
                    
                    # Ensure current_selection only contains valid options
                    valid_selection = [et for et in current_selection if et in available_edge_types]
                    
                    # Create a dynamic key for multiselect to force refresh when options change
                    edge_types_hash = hash(tuple(sorted(available_edge_types)))
                    multiselect_key = f"edge_multiselect_{edge_types_hash}"
                    
                    # Multiselect for edge types
                    selected_edges = st.multiselect(
                        label="Choose edge types:",
                        options=available_edge_types,
                        default=valid_selection,
                        key=multiselect_key
                    )

                    # Select All / Select None buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Select All", key="select_all_edges", use_container_width=True):
                            st.session_state.selected_edge_types = available_edge_types.copy()
                            # Remove multiselect's session state to force reload
                            for key in list(st.session_state.keys()):
                                if key.startswith("edge_multiselect_"):
                                    del st.session_state[key]
                            st.rerun()
                    with col2:
                        if st.button("Select None", key="select_none_edges", use_container_width=True):
                            st.session_state.selected_edge_types = []
                            # Remove multiselect's session state to force reload
                            for key in list(st.session_state.keys()):
                                if key.startswith("edge_multiselect_"):
                                    del st.session_state[key]
                            st.rerun()
                    
                    # Update session state
                    st.session_state.selected_edge_types = selected_edges
                else:
                    st.info("Edge types will be generated automatically based on your selected entities.")
                    
            db = st.text_input("DB path", "E:/LabWork/BioMedGraphica-Conn") # TODO: make this configurable, currently hardcoded for testing

            # ---------- Run Controls ----------
            btn_l, btn_r = st.columns([1, 1])
            with btn_l:
                if st.button("⬅ Back", key="step2_back", use_container_width=True):
                    st.session_state.step1_open, st.session_state.step2_open = True, False
                    st.rerun()

            with btn_r:
                run_button_clicked = st.button("▶️ Submit Processing Job", key="step2_run", use_container_width=True)

            if run_button_clicked:

                entity_cfgs = []
                for e in st.session_state.entities:
                    if e["feature_label"].strip():
                        id_info = get_id_info_from_display(e["entity_type"], e["id_type"])
                        entity_cfgs.append(dict(
                            feature_label=e["feature_label"],
                            entity_type=e["entity_type"].lower(),
                            id_type=id_info["actual_id"],
                            match_mode=id_info["match_mode"],
                            file_path=e["file_path"],
                            fill0=e["fill0"]
                        ))

                label_cfg = None
                if st.session_state.label_path:
                    label_cfg = dict(
                        feature_label="label",
                        entity_type="label",
                        id_type="",
                        file_path=st.session_state.label_path,
                        fill0=False
                    )

                final_payload = dict(
                    job_id=job_id,
                    entities_cfgs=entity_cfgs,
                    label_cfg=label_cfg,
                    database_path=db,
                    output_dir=job_data_output_dir,
                    finalize=dict(
                        file_order=st.session_state.file_order,
                        apply_zscore=st.session_state.apply_zscore,
                        edge_types=st.session_state.selected_edge_types,
                    )
                )

                # Debug config payload
                st.code(json.dumps(final_payload, indent=2), language="json")

                # Submit to backend (FastAPI + Celery)
                with st.spinner("🚀 Submitting job to backend..."):
                    task_id = submit_async_processing_task(final_payload)
                    st.session_state["submitted_task_id"] = task_id
                    st.success(f"✅ Job submitted successfully! Task ID: `{task_id}`")

            # ---------- Async Task Status ----------
            if "submitted_task_id" in st.session_state:
                with st.expander("📊 Processing Status", expanded=True):
                    task_id = st.session_state.submitted_task_id
                    status = check_task_status(task_id)

                    st.markdown(f"**Task ID**: `{task_id}`")
                    st.markdown(f"**Status**: `{status.get('state', 'unknown')}`")

                    # Check for specific states
                    if status.get("state") == "awaiting_mapping":
                        st.info("🔎 Soft match candidates detected — please resolve mappings.")
                        mapping_candidates = status["mapping_candidates"]

                        confirmed_mappings = render_mapping_selector(mapping_candidates)

                        if confirmed_mappings:
                            # Submit confirmed mappings to backend 
                            # backend/api/processing.py @router.post("/submit-mappings")
                            submit_mappings_to_backend(task_id, confirmed_mappings)
                            st.success("✅ Mappings submitted. Processing will resume automatically.")
                            st.rerun()

                    elif status.get("state") == "SUCCESS":
                        st.success("🎉 Processing completed!")
                        st.download_button(
                            label="📥 Download Result",
                            data=status["result_file_bytes"],
                            file_name="biomedgraphica_output.zip"
                        )
                        del st.session_state.submitted_task_id

                    elif status.get("state") == "FAILURE":
                        st.error("❌ Task failed. Please check logs or retry.")
                        del st.session_state.submitted_task_id

                    else:
                        st.info("⏳ Still processing. Please wait or refresh.")


    with main_right:
        # Graph
        render_knowledge_graph(job_manager)

        st.divider()

        # Status info box
        render_log_console()

    # # ---------- style tweaks ----------

    # </style>""", unsafe_allow_html=True)