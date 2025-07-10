# components/knowledge_graph.py

import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

# Define entity types and their colors
ENTITY_TYPES_COLORS = {
    "Promoter": "black",
    "Gene": "#f4cccc",
    "Transcript": "#a2c4c9",
    "Protein": "#fce5cd",
    "Pathway": "#d9ead3",
    "Exposure": "#ead1dc",
    "Metabolite": "#f9cb9c",
    "Drug": "#b6b6b6",
    "Microbiota": "#f6b26b",
    "Phenotype": "#cfe2f3",
    "Disease": "#f4cccc"
}

# Fixed node positions
NODE_POSITIONS = {
    "Promoter": (-300, 0),
    "Gene": (-200, -50),
    "Transcript": (-100, 0),
    "Protein": (-50, 100),
    "Pathway": (0, -30),
    "Exposure": (80, -150),
    "Metabolite": (120, 150),
    "Drug": (200, -100),
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

    # 读取选中的实体类型（从 session_state.entities）
    selected_entities = []
    if "entities" in st.session_state:
        selected_entities = [
            ent["entity_type"] for ent in st.session_state.entities if ent["entity_type"]
        ]

    # 构建图
    G = nx.DiGraph()
    G.add_edges_from(EDGES)

    # 构建 Pyvis 图
    net = Network(height="500px", width="100%", directed=True)
    net.barnes_hut()  # 使用更平滑的力导引引擎（物理布局被禁用）

    # 添加节点
    for node in G.nodes():
        base_color = ENTITY_TYPES_COLORS.get(node, "gray")
        is_selected = node in selected_entities
        border_color = "#FFD700" if is_selected else "#333"
        border_width = 6 if is_selected else 1

        net.add_node(
            node,
            label=node,
            color=base_color,
            borderWidth=border_width,
            borderWidthSelected=border_width,
            x=NODE_POSITIONS[node][0],
            y=NODE_POSITIONS[node][1],
            fixed={"x": True, "y": True},
        )

    # 添加边
    for src, dst in G.edges():
        highlight = src in selected_entities and dst in selected_entities
        net.add_edge(
            src,
            dst,
            color="#FFD700" if highlight else "#888",
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
        components.html(html_content, height=550, scrolling=True)
