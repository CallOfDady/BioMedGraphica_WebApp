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
    from .entity_row import analyze_knowledge_graph_connectivity
    connectivity_analysis = analyze_knowledge_graph_connectivity(st.session_state.get("entities", []))
    
    missing_nodes = connectivity_analysis.get("missing_nodes", [])
    broken_paths = connectivity_analysis.get("broken_paths", [])
    path_edges = connectivity_analysis.get("path_edges", [])

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
        # Check if this edge is part of a broken path
        is_broken_edge = False
        for broken_src, broken_dst in broken_paths:
            if (src == broken_src and dst == broken_dst) or (src == broken_dst and dst == broken_src):
                is_broken_edge = True
                break
        
        # Check if this edge is part of the connectivity path
        is_path_edge = (src, dst) in path_edges or (dst, src) in path_edges
        
        # Check if this edge connects selected nodes directly
        connects_selected = src in selected_entities and dst in selected_entities
        
        # Color logic:
        # - Red: only for path edges that involve missing nodes or broken paths
        # - Black: edges that connect selected nodes directly
        # - Gray: normal edges
        if is_broken_edge:
            edge_color = error_color  # red for broken edges
            edge_width = 2
        elif is_path_edge and missing_nodes:
            # Only color red if it's a path edge AND there are missing nodes
            edge_involves_missing = src in missing_nodes or dst in missing_nodes
            if edge_involves_missing:
                edge_color = error_color  # red for path edges involving missing nodes
                edge_width = 2
            elif connects_selected:
                edge_color = selected_color  # black for selected connections
                edge_width = 3
            else:
                edge_color = "#888"  # gray for normal edges
                edge_width = 1
        elif connects_selected:
            edge_color = selected_color  # black for selected connections
            edge_width = 3
        else:
            edge_color = "#888"  # gray for normal edges
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
    if missing_nodes or broken_paths:
        st.markdown("**🔍 Graph Analysis:**")
        if missing_nodes:
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
                
        if broken_paths:
            st.markdown("🔴 **Disconnected paths:**")
            for src, dst in broken_paths:
                st.markdown(f"  • {src} ↔ {dst}")
    else:
        if selected_entities:
            st.markdown("✅ **All selected entities are connected**")
