# components/knowledge_graph.py

import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
from frontend.constants import ENTITY_TYPES_COLORS, NODE_POSITIONS, EDGES
import os

selected_color = "black"  # Color for selected nodes and edges
error_color = "#ff0000"  # Color for errors (missing nodes, broken paths)

def render_knowledge_graph(job_manager):
    st.subheader("🧠 Knowledge Graph")
    
    # Retrieve selected entity types (from session_state.entities)
    selected_entities = []
    if "entities" in st.session_state:
        selected_entities = [
            ent["entity_type"] for ent in st.session_state.entities if ent["entity_type"]
        ]
    
    # Analyze connectivity of the knowledge graph
    connectivity_analysis = analyze_knowledge_graph_connectivity(st.session_state.get("entities", []))
    
    missing_nodes = connectivity_analysis.get("missing_nodes", [])
    edges_on_paths = connectivity_analysis.get("edges_on_paths", [])

    # Create a directed graph
    G = nx.DiGraph()
    G.add_edges_from(EDGES)

    # Create a Pyvis network
    net = Network(height="500px", width="100%", directed=True)
    net.barnes_hut()  # Use a smoother force-directed engine (physics layout is disabled)

    # Add nodes with fixed positions
    for node in G.nodes():
        is_selected = node in selected_entities
        is_missing = node in missing_nodes
        
        # Determine node color and border based on state
        if is_missing:
            node_color = "#ffcccc"  # red background for missing nodes
            border_color = error_color  # red border
            border_width = 2
        elif is_selected:
            node_color = ENTITY_TYPES_COLORS.get(node, "gray")
            border_color = selected_color
            border_width = 3
        else:
            node_color = ENTITY_TYPES_COLORS.get(node, "gray")
            border_color = "#333"
            border_width = 1

        net.add_node(
            node,
            label=node,
            color={
                "background": node_color,
                "border": border_color,
                "highlight": {
                    "background": node_color,
                    "border": border_color
                }
            },
            borderWidth=border_width,
            borderWidthSelected=border_width,
            x=NODE_POSITIONS[node][0],
            y=NODE_POSITIONS[node][1],
            fixed={"x": True, "y": True}
        )

    # Add edges with highlighting
    for src, dst in G.edges():
        # This edge is part of at least one chosen path (either direction)
        is_path_edge = (src, dst) in edges_on_paths or (dst, src) in edges_on_paths

        # The edge directly connects two user-selected nodes
        connects_selected = src in selected_entities and dst in selected_entities

        # At least one endpoint of this edge is currently missing (virtual-needed)
        edge_involves_missing = (src in missing_nodes) or (dst in missing_nodes)

        if is_path_edge and edge_involves_missing:
             # On a chosen path AND touches a missing node → highlight as an unresolved requirement
            edge_color = error_color
            edge_width = 2
        elif is_path_edge and connects_selected:
             # On a chosen path AND both endpoints are selected → emphasize the confirmed connection
            edge_color = selected_color # Black
            edge_width = 3
        elif connects_selected:
            # Not on a chosen path but directly connects two selected nodes
            edge_color = selected_color # Black
            edge_width = 3
        elif is_path_edge:
            # On a chosen path but does not touch a missing node and is not a selected-to-selected edge
            edge_color = "#888" # Gray
            edge_width = 1
        else:
            # Others
            edge_color = "#888" # Gray
            edge_width = 1

        net.add_edge(
            src,
            dst,
            color=edge_color,
            width=edge_width,
            arrowStrikethrough=False
        )

    net.set_options("""
    var options = {
      "nodes": {
        "shape": "ellipse",
        "font": {"size": 18},
        "shadow": false
      },
      "edges": {
        "arrows": {
          "to": {"enabled": true}
        },
        "smooth": false
      },
      "interaction": {
        "hover": true,
        "dragNodes": false,
        "zoomView": true,
        "dragView": true
      },
      "physics": {
        "enabled": false
      }
    }
    """)

    net.save_graph("temp_graph.html")
    
    # Move the graph to the session's temp directory
    if "job_id" in st.session_state:
        job_dir = job_manager.get_job_dir()
        temp_graph_path = job_dir / "temp_graph.html"
        
        # Move the file to temp directory
        import shutil
        shutil.move("temp_graph.html", str(temp_graph_path))
        
        # Read from temp directory
        with open(temp_graph_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    else:
        # Fallback: read from current directory if no session
        with open("temp_graph.html", "r", encoding="utf-8") as f:
            html_content = f.read()

    # Inject the drawing code before the </script> that closes Vis.js config
    injected_code = """
    network.on("afterDrawing", function (ctx) {
      // First ellipse
      ctx.beginPath();
      ctx.ellipse(-240, 0, 140, 90, 0, 0, 2 * Math.PI);
      ctx.strokeStyle = "black";
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 4]);
      ctx.stroke();

      // Second ellipse
      ctx.beginPath();
      ctx.ellipse(-140, 50, 260, 200, 0, 0, 2 * Math.PI);
      ctx.strokeStyle = "black";
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 4]);
      ctx.stroke();

      // Reset line dash
      ctx.setLineDash([]);

      // Draw labels
      ctx.font = "bold 20px Arial";
      ctx.fillStyle = "black";
      ctx.fillText("Nucleus", -270, 60);
      ctx.fillText("Cell", -150, 220);
    });
    """

    # Insert before last </script>
    html_content = html_content.replace("</script>", injected_code + "\n</script>")

    components.html(html_content, height=550, scrolling=True)
    
    # Display legend and status information
    if selected_entities and not missing_nodes:
        st.markdown("✅ **All selected entities are connected**")
    elif missing_nodes:
        st.markdown("**🔍 Graph Analysis:**")
        st.markdown(f"🔴 **Missing nodes for connectivity:** {', '.join(missing_nodes)}")
        
        # Quick add missing nodes button
        if st.button("🔧 Quick add missing nodes", key="quick_add_missing"):
            import uuid
            for missing_node in missing_nodes:
                st.session_state.entities.append(dict(
                    uuid=str(uuid.uuid4()),
                    fill0=True,  # Virtual node
                    feature_label=missing_node.lower(),  # Use lowercase label
                    entity_type=missing_node,
                    id_type="",
                    file_path=""
                ))
            from .entity_row import log_to_console
            log_to_console(f"🔧 Quick-added missing virtual nodes: {', '.join(missing_nodes)}")
            st.rerun()

def analyze_knowledge_graph_connectivity(
    entities: list,
    max_hops_per_path: int = 5
) -> dict:
    #  User-selected entity types
    selected_types = set()
    for ent in entities:
        t = (ent.get("entity_type") or "").strip()
        if t:
            selected_types.add(t)

    core_order = ["Promoter", "Gene", "Transcript", "Protein"]
    core_set = set(core_order)

    if not selected_types:
        return {
            "connected": True,
            "missing_nodes": [],
            "suggestions": [],
            "edges_on_paths": [],
            "path_options": []
        }

    # Construct undirected graph
    G = nx.DiGraph()
    G.add_edges_from(EDGES)
    UG = G.to_undirected()

    missing_nodes: list[str] = []
    suggestions: list[str] = []
    edges_on_paths: set[tuple[str, str]] = set()
    path_options: list[dict] = []

    def add_edges_on_paths(path_seq: list[str]):
        for k in range(len(path_seq) - 1):
            u, v = path_seq[k], path_seq[k + 1]
            if (u, v) in EDGES:
                edges_on_paths.add((u, v))
            elif (v, u) in EDGES:
                edges_on_paths.add((v, u))

    def all_shortest_paths_bound(src: str, dst: str) -> list[list[str]]:
        """Return all shortest paths within hop bound; empty list if none."""
        try:
            p = nx.shortest_path(UG, src, dst)
            L = len(p) - 1
            if L > max_hops_per_path:
                return []
            return [path for path in nx.all_shortest_paths(UG, src, dst) if len(path) - 1 == L]
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            return []
        
    def has_direct_edge(u: str, v: str) -> bool:
        """Check if there is a direct (undirected) edge between u and v in EDGES."""
        return (u, v) in EDGES or (v, u) in EDGES

    def core_segment_from(cn: str) -> list[str]:
        """Return the core segment from core node `cn` to Protein, inclusive."""
        i = core_order.index(cn)
        j = core_order.index("Protein")
        return core_order[i:j+1] if i <= j else [cn]

    # core bone auto-fill
    selected_core = list(selected_types.intersection(core_set))
    core_autofill_set: set[str] = set()
    if selected_core:
        idxs = [core_order.index(n) for n in selected_core]
        start_idx = min(idxs)
        protein_idx = core_order.index("Protein")
        core_path = core_order[start_idx:protein_idx + 1] if start_idx <= protein_idx else [core_order[start_idx]]

        core_autofill_set = set(core_path)

        # Mark missing core nodes, force fill
        for n in core_path:
            if n not in selected_types and n not in missing_nodes:
                missing_nodes.append(n)
                suggestions.append(f"Add '{n}' as virtual node (required by core pathway)")
        # Highlight core edges
        for k in range(len(core_path) - 1):
            u, v = core_path[k], core_path[k + 1]
            if (u, v) in EDGES or (v, u) in EDGES:
                edges_on_paths.add((u, v) if (u, v) in EDGES else (v, u))

    # Process non-core node pairs
    def process_pair(src: str, dst: str):
        if selected_core:
            # core_path is already defined, try to connect via core
            for cn in core_path:
                if has_direct_edge(dst, cn):
                    # Path：dst → cn → ... → Protein
                    segment = core_segment_from(cn)          # [cn, ..., Protein]
                    combined = [dst] + segment
                    # Highlight edges
                    add_edges_on_paths(combined)
                    path_options.append({
                        "pair": (src, dst),
                        "path": combined,
                        "missing_nodes": [n for n in combined if n not in selected_types]
                    })
                    return

        # Get all shortest paths
        cands = all_shortest_paths_bound(src, dst)
        if not cands:
            return  # Should not happen as it's fully connected graph

        # Check missing nodes on each path (excluding selected and core autofill)
        per_path_missing = []
        for path in cands:
            miss = [n for n in path if n not in selected_types and n not in core_autofill_set]
            per_path_missing.append(set(miss))

        # Add edges and path options
        for path in cands:
            add_edges_on_paths(path)
            path_options.append({
                "pair": (src, dst),
                "path": path,
                "missing_nodes": [n for n in path if n not in selected_types]
            })

        # If there exists a "zero-missing" shortest path → already connected: do not add new missing
        if any(len(miss) == 0 for miss in per_path_missing):
            return

        # Otherwise: highlight the all missing nodes that appeared in the shortest paths
        needed_union = set().union(*per_path_missing) if per_path_missing else set()
        for n in sorted(needed_union):
            if n not in missing_nodes:
                missing_nodes.append(n)
        if needed_union:
            choices = ", ".join(sorted(needed_union))
            suggestions.append(
                f"Add one of {{{choices}}} to connect {src} and {dst} via a shortest path"
            )

    if selected_core:
        # Non-core nodes only connect to Protein
        anchor = "Protein"
        for target in [n for n in selected_types if n not in core_set]:
            if target == anchor:
                continue
            process_pair(anchor, target)
    else:
        # No core: pairwise processing
        endpoints = list(selected_types)
        for i in range(len(endpoints)):
            for j in range(i + 1, len(endpoints)):
                process_pair(endpoints[i], endpoints[j])

    # Final connectivity status
    connected = len(missing_nodes) == 0
    return {
        "connected": connected,
        "missing_nodes": missing_nodes,
        "suggestions": suggestions,
        "edges_on_paths": list(edges_on_paths),
        "path_options": path_options
    }

def generate_edge_types_from_entities(entities: list) -> list:
    """
    Generate edge types based on selected entities and the predefined edges.
    """
    
    # Get only user-selected entity types (not including connectivity analysis)
    selected_types = set()
    for ent in entities:
        if ent.get("entity_type", "").strip():
            selected_types.add(ent.get("entity_type"))
    
    # Generate edge types only for actually selected entities
    edge_types = []
    for source, target in EDGES:
        if source in selected_types and target in selected_types:
            edge_type = f"{source}-{target}"
            if edge_type not in edge_types:
                edge_types.append(edge_type)
    
    return sorted(edge_types)