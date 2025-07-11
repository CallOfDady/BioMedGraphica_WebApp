# components/knowledge_graph.py

import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

selected_color = "#3f704d"  # Color for selected nodes and edges

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


def render_knowledge_graph():
    st.subheader("🧠 Knowledge Graph")

    # Retrieve selected entity types (from session_state.entities)
    selected_entities = []
    if "entities" in st.session_state:
        selected_entities = [
            ent["entity_type"] for ent in st.session_state.entities if ent["entity_type"]
        ]

    # Create a directed graph
    G = nx.DiGraph()
    G.add_edges_from(EDGES)

    # Create a Pyvis network
    net = Network(height="500px", width="100%", directed=True)
    net.barnes_hut()  # Use a smoother force-directed engine (physics layout is disabled)

    # Add nodes with fixed positions
    for node in G.nodes():
      is_selected = node in selected_entities

      net.add_node(
          node,
          label=node,
          color={
              "background": ENTITY_TYPES_COLORS.get(node, "gray"),
              "border": selected_color if is_selected else "#333",
              "highlight": {
                  "background": ENTITY_TYPES_COLORS.get(node, "gray"),
                  "border": selected_color
              }
          },
          borderWidth=3 if is_selected else 1,
          borderWidthSelected=3,
          x=NODE_POSITIONS[node][0],
          y=NODE_POSITIONS[node][1],
          fixed={"x": True, "y": True}
      )

    # Add edges with highlighting
    for src, dst in G.edges():
        highlight = src in selected_entities and dst in selected_entities
        net.add_edge(
            src,
            dst,
            color=selected_color if highlight else "#888",
            width=3 if highlight else 1,
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
