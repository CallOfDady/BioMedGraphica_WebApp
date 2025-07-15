# components/entity_row.py

import streamlit as st
import os
import streamlit_nested_layout
from biomedgraphica_app_constants import ENTITY_TYPES, ID_TYPES
from .knowledge_graph import ENTITY_TYPES_COLORS
from utils.temp_manager import get_temp_manager

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
    # Use entity dict value as the source of truth for text input
    value = ent.get(field, "")
    new_value = st.text_input(label, value=value, key=key, help=help)
    ent[field] = new_value
    return new_value


def bind_selectbox(label: str, options: list[str], key: str, ent: dict, field: str, disabled=False, fallback=None, help: str | None = None):
    # Get current value from session state first (for immediate UI response), then from entity dict
    session_value = st.session_state.get(key)
    entity_value = ent.get(field, fallback or (options[0] if options else ""))
    
    # Special handling for different field types
    if field == "entity_type" and ent.get("auto_fill_type"):
        # For auto-filled entity types, prefer entity dict value
        current_value = entity_value
    elif field == "id_type":
        # For ID type, always prioritize session state if it exists and is valid
        if session_value is not None and session_value in options:
            current_value = session_value
        else:
            current_value = entity_value
    elif session_value is not None and session_value in options:
        # For other fields, use session state if available and valid
        current_value = session_value
    else:
        # Fallback to entity dict value
        current_value = entity_value
    
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
            # Delete associated file before removing entity
            temp_manager = get_temp_manager()
            entity_label = ent.get("feature_label", "").strip()
            if entity_label:
                temp_manager.delete_uploaded_file(entity_label)
                log_to_console(f"🗑️ Deleted files for entity: `{entity_label}`")
            return True

    # ---------- Color Box ----------
    with col_color:
        # Get current entity type from session state first (for immediate response), then from entity dict
        entity_type_key = f"typ_{uuid}"
        session_entity_type = st.session_state.get(entity_type_key)
        entity_dict_type = ent.get("entity_type", "")
        
        # If auto-filled, prefer entity dict value; otherwise use session state for immediate response
        if ent.get("auto_fill_type"):
            current_entity_type = entity_dict_type
        else:
            current_entity_type = session_entity_type if session_entity_type is not None else entity_dict_type
        
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
            # Get current node type from session state first, then from entity dict
            node_type_key = f"ntype_{uuid}"
            session_node_type = st.session_state.get(node_type_key)
            
            if session_node_type is not None:
                current_node_type = session_node_type
            else:
                current_node_type = "Virtual Node" if ent.get("fill0", False) else "Real Node"
            
            # Find the index
            options = ["Real Node", "Virtual Node"]
            index = 0 if current_node_type == "Real Node" else 1
            
            node_type = st.selectbox(
                label="Node Type",
                options=options,
                index=index,
                key=node_type_key,
                help="Select the type of node for this entity."
            )
            
            # Update the fill0 field based on node type
            old_is_virtual = ent.get("fill0", False)
            is_virtual = node_type == "Virtual Node"
            ent["fill0"] = is_virtual
            
            # Clear file path and id_type when switching to virtual node
            if is_virtual:
                ent["file_path"] = ""
                ent["id_type"] = ""
                
                # Auto-fill label when switching to virtual node
                if not old_is_virtual and ent.get("entity_type", "").strip():
                    ent["feature_label"] = ent["entity_type"].lower()
                    log_to_console(f"🏷️ Auto-filled virtual node label: `{ent['entity_type'].lower()}`")

        # Label
        with upper[1]:
            bind_input("Label", key=f"lab_{uuid}", ent=ent, field="feature_label", help="Enter a label for this entity.")

        lower = st.columns([1, 1])

        # Entity Type
        with lower[0]:
            old_entity_type = ent.get("entity_type", "")
            
            bind_selectbox(
                label="Entity Type",
                options=ENTITY_TYPES,
                key=f"typ_{uuid}",
                ent=ent,
                field="entity_type",
                help="Select the type of entity."
            )
            
            # Auto-fill label for virtual nodes when entity type changes
            new_entity_type = ent.get("entity_type", "")
            if (ent.get("fill0", False) and  # is virtual node
                new_entity_type != old_entity_type and  # entity type changed
                new_entity_type.strip()):  # new entity type is not empty
                ent["feature_label"] = new_entity_type.lower()
                log_to_console(f"🏷️ Auto-filled virtual node label: `{new_entity_type.lower()}`")

        # ID Type
        with lower[1]:
            if ent.get("fill0"):
                st.selectbox("ID Type", ["N/A"], disabled=True, key=f"idt_{uuid}_disabled")
            else:
                # Get current entity type from session state or entity dict
                entity_type_key = f"typ_{uuid}"
                session_entity_type = st.session_state.get(entity_type_key)
                entity_dict_type = ent.get("entity_type", "")
                
                # If auto-filled, prefer entity dict value; otherwise use session state
                if ent.get("auto_fill_type"):
                    current_entity_type = entity_dict_type
                else:
                    current_entity_type = session_entity_type if session_entity_type is not None else entity_dict_type
                
                opts = ID_TYPES.get(current_entity_type, [""])
                
                # If entity type changed, reset ID type to first option
                current_id_type = ent.get("id_type", "")
                if current_id_type not in opts:
                    ent["id_type"] = opts[0] if opts else ""
                
                # Use the enhanced bind_selectbox for ID Type as well
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
            # File upload with automatic cleanup when uploader is cleared
            upf = st.file_uploader("Upload", type=["csv", "tsv", "txt"],
                                   key=f"upl_{uuid}", label_visibility="collapsed")
            
            # Get temp manager and handle file upload changes
            temp_manager = get_temp_manager()
            
            # Determine entity label for filename
            entity_label = ent.get("feature_label", "").strip()
            if not entity_label and upf is not None:
                # Use filename without extension as entity label
                entity_label = os.path.splitext(upf.name)[0]
            elif not entity_label:
                # No file uploaded and no label - use UUID as fallback
                entity_label = f"entity_{uuid}"
            
            # Use auto-cleanup method to handle file upload/clear
            previous_file_key = f"_had_file_{uuid}"
            saved_path = temp_manager.handle_file_upload_change(upf, entity_label, previous_file_key)
            
            if saved_path:
                # File was uploaded
                # Check if this is a new upload (avoid re-processing same file)
                if ent.get("_uploaded_file_path") == saved_path:
                    return False
                
                ent["file_path"] = saved_path
                ent["_uploaded_file_path"] = saved_path
                ent["_uploaded_once"] = True
                log_to_console(f"📁 File saved: `{os.path.basename(saved_path)}` → `{saved_path}`")

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
            else:
                # File was cleared (upf is None) - automatic cleanup was already handled
                # Just update the entity state
                if ent.get("_uploaded_once"):
                    ent["file_path"] = ""
                    ent["_uploaded_file_path"] = ""
                    ent["_uploaded_once"] = False
                    log_to_console(f"🗑️ File cleared for entity: `{entity_label}`")
                    st.rerun()

    st.markdown("<hr style='margin-top: 0.5rem; margin-bottom: 0.8rem;'>", unsafe_allow_html=True)
    return False


# ---------- VALIDATION FUNCTIONS ----------

def validate_entities(entities: list) -> dict:
    """
    validate all entities for completeness
    Returns a dictionary with validation results
    """
    errors = []
    warnings = []
    
    for i, ent in enumerate(entities):
        entity_name = ent.get("feature_label", f"Entity {i+1}")
        is_virtual = ent.get("fill0", False)
        
        if is_virtual:
            # Virtual node only needs label and entity type
            if not ent.get("feature_label", "").strip():
                errors.append(f"Virtual node {i+1}: Missing label")
            if not ent.get("entity_type", "").strip():
                errors.append(f"Virtual node '{entity_name}': Missing entity type")
        else:
            # Real node needs to check all fields
            if not ent.get("feature_label", "").strip():
                errors.append(f"Real node {i+1}: Missing label")
            if not ent.get("entity_type", "").strip():
                errors.append(f"Real node '{entity_name}': Missing entity type")
            if not ent.get("id_type", "").strip():
                errors.append(f"Real node '{entity_name}': Missing ID type")
            if not ent.get("file_path", "").strip():
                errors.append(f"Real node '{entity_name}': Missing uploaded file")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def check_label_file(label_path: str) -> dict:
    """
    check if the label file is valid
    """
    if not label_path or not label_path.strip():
        return {
            "valid": False,
            "errors": ["Sample label file is required"],
            "warnings": []
        }
    
    return {
        "valid": True,
        "errors": [],
        "warnings": []
    }


def analyze_knowledge_graph_connectivity(entities: list) -> dict:
    """
    check connectivity of the knowledge graph based on selected entities
    """
    from .knowledge_graph import EDGES
    
    # get user-selected entity types
    selected_types = set()
    for ent in entities:
        if ent.get("entity_type", "").strip():
            selected_types.add(ent.get("entity_type"))
    
    # Define core pathway nodes
    core_pathway_nodes = {"Promoter", "Gene", "Transcript", "Protein"}
    
    # Check if any of Promoter, Gene, or Transcript is selected
    # If so, the full core path is required
    trigger_nodes = {"Promoter", "Gene", "Transcript"}
    selected_trigger_nodes = selected_types.intersection(trigger_nodes)
    
    # Early return only if no entities selected or no core path requirement
    if len(selected_types) == 0:
        return {
            "connected": True,
            "missing_nodes": [],
            "broken_paths": [],
            "suggestions": [],
            "path_edges": []
        }
    
    # If only one entity is selected and it's not a trigger node, no connectivity check needed
    if len(selected_types) == 1 and not selected_trigger_nodes:
        return {
            "connected": True,
            "missing_nodes": [],
            "broken_paths": [],
            "suggestions": [],
            "path_edges": []
        }
    
    # If any trigger node is selected, we need the complete core pathway
    if selected_trigger_nodes:
        # Add all core pathway nodes to the analysis
        extended_selected_types = selected_types.copy()
        extended_selected_types.update(core_pathway_nodes)
    else:
        extended_selected_types = selected_types
    
    # generate a directed graph from the edges
    import networkx as nx
    G = nx.DiGraph()
    G.add_edges_from(EDGES)
    
    # convert to undirected graph for connectivity analysis
    UG = G.to_undirected()
    
    # Add core path edges with weights
    # Core Path：Promoter → Gene → Transcript → Protein → Pathway
    core_path_edges = [
        ("Promoter", "Gene"), ("Gene", "Transcript"), ("Transcript", "Protein"),
        ("Protein", "Pathway"), ("Protein", "Disease"), ("Protein", "Phenotype")
    ]
    
    # Add core path edges with low weight
    for edge in UG.edges():
        if edge in core_path_edges or (edge[1], edge[0]) in core_path_edges:
            UG[edge[0]][edge[1]]['weight'] = 1  # Core path has low weight (high priority)
        else:
            UG[edge[0]][edge[1]]['weight'] = 2  # Other paths have high weight

    missing_nodes = []
    broken_paths = []
    suggestions = []
    path_edges = []  # Store edges in the path
    
    # First, check if we need to add core pathway nodes
    if selected_trigger_nodes:
        # Define the core path order
        core_path_order = ["Promoter", "Gene", "Transcript", "Protein"]
        
        # Find the earliest and latest selected trigger nodes in the core path
        selected_indices = []
        for node in selected_trigger_nodes:
            if node in core_path_order:
                selected_indices.append(core_path_order.index(node))
        
        # Always ensure we have Protein (since it's needed for protein-protein interactions)
        if "Protein" not in selected_types:
            missing_nodes.append("Protein")
            suggestions.append("Add 'Protein' as virtual node (required for core pathway)")
        
        # Add missing nodes between selected trigger nodes and Protein
        min_index = min(selected_indices)
        protein_index = core_path_order.index("Protein")
        
        # Add all missing nodes from the earliest selected node to Protein
        for i in range(min_index, protein_index):
            node = core_path_order[i]
            if node not in selected_types and node not in missing_nodes:
                missing_nodes.append(node)
                suggestions.append(f"Add '{node}' as virtual node (required for core pathway)")
    
    # Update extended_selected_types to include missing core pathway nodes
    extended_selected_types = selected_types.copy()
    extended_selected_types.update(missing_nodes)
    
    # Check all pairs of selected types (using extended types for analysis)
    extended_list = list(extended_selected_types)
    for i in range(len(extended_list)):
        for j in range(i + 1, len(extended_list)):
            source = extended_list[i]
            target = extended_list[j]
            
            try:
                # Check if there's a path between source and target
                if nx.has_path(UG, source, target):
                    # Use weighted shortest path algorithm
                    path = nx.shortest_path(UG, source, target, weight='weight')

                    # Record edges in the path
                    for k in range(len(path) - 1):
                        edge = (path[k], path[k + 1])
                        # Check for forward and reverse edges
                        if edge in EDGES:
                            path_edges.append(edge)
                        elif (edge[1], edge[0]) in EDGES:
                            path_edges.append((edge[1], edge[0]))
                    
                    # Check if there are missing intermediate nodes (beyond core pathway)
                    for node in path[1:-1]:  # Exclude start and end nodes
                        if node not in extended_selected_types:
                            if node not in missing_nodes:
                                missing_nodes.append(node)
                                suggestions.append(f"Add '{node}' as virtual node to connect {source} and {target}")
                else:
                    broken_paths.append((source, target))
            except nx.NetworkXNoPath:
                broken_paths.append((source, target))
    
    return {
        "connected": len(missing_nodes) == 0 and len(broken_paths) == 0,
        "missing_nodes": missing_nodes,
        "broken_paths": broken_paths,
        "suggestions": suggestions,
        "path_edges": list(set(path_edges))  # Remove duplicates
    }


def generate_edge_types_from_entities(entities: list) -> list:
    """
    Generate edge types based on selected entities and the predefined edges.
    """
    from .knowledge_graph import EDGES
    
    # check connectivity of the knowledge graph based on selected entities
    connectivity_analysis = analyze_knowledge_graph_connectivity(entities)
    selected_types = set()
    
    for ent in entities:
        if ent.get("entity_type", "").strip():
            selected_types.add(ent.get("entity_type"))
    
    # Add suggested virtual nodes
    for missing_node in connectivity_analysis["missing_nodes"]:
        selected_types.add(missing_node)
    
    # Generate edge types
    edge_types = []
    for source, target in EDGES:
        if source in selected_types and target in selected_types:
            edge_type = f"{source}-{target}"
            if edge_type not in edge_types:
                edge_types.append(edge_type)
    
    return sorted(edge_types)