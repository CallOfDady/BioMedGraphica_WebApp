import copy
import streamlit as st

from frontend.components.processing_summary import render_processing_summary


def build_mock_status():
    return {
        "result": {
            "stats": {
                "sample_count": 1280,
                "total_selected_edges": 342,
                "entity_count": 8,
                "entity_stats": [
                    {
                        "feature_label": "Gene",
                        "entity_type": "biological_entity",
                        "input_source": "file",
                        "input_feature_count": 320,
                        "mapped_count": 285,
                    },
                    {
                        "feature_label": "Protein",
                        "entity_type": "biological_entity",
                        "input_source": "file",
                        "input_feature_count": 250,
                        "mapped_count": 198,
                    },
                    {
                        "feature_label": "Disease",
                        "entity_type": "medical_entity",
                        "input_source": "file",
                        "input_feature_count": 180,
                        "mapped_count": 141,
                    },
                    {
                        "feature_label": "Drug",
                        "entity_type": "chemical_entity",
                        "input_source": "file",
                        "input_feature_count": 145,
                        "mapped_count": 117,
                    },
                    {
                        "feature_label": "Pathway",
                        "entity_type": "knowledge_graph_entity",
                        "input_source": "file",
                        "input_feature_count": 120,
                        "mapped_count": 72,
                    },
                    {
                        "feature_label": "Tissue",
                        "entity_type": "anatomy_entity",
                        "input_source": "file",
                        "input_feature_count": 90,
                        "mapped_count": 51,
                    },
                    {
                        "feature_label": "Cell Type",
                        "entity_type": "biological_entity",
                        "input_source": "file",
                        "input_feature_count": 160,
                        "mapped_count": 132,
                    },
                    {
                        "feature_label": "Custom Virtual Bucket",
                        "entity_type": "virtual_group",
                        "input_source": "virtual",
                        "input_feature_count": 0,
                        "mapped_count": 0,
                    },
                ],
                "edge_type_counts": {
                    "ASSOCIATED_WITH": 104,
                    "INTERACTS_WITH": 83,
                    "TREATS": 57,
                    "LOCATED_IN": 46,
                    "PART_OF": 29,
                    "CAUSES": 23,
                },
            }
        }
    }


def build_adjusted_status():
    status = build_mock_status()
    stats = status["result"]["stats"]

    st.sidebar.header("Mock Data Control")

    stats["sample_count"] = st.sidebar.number_input(
        "Sample count",
        min_value=0,
        value=stats["sample_count"],
        step=10,
    )

    stats["total_selected_edges"] = st.sidebar.number_input(
        "Selected edges",
        min_value=0,
        value=stats["total_selected_edges"],
        step=1,
    )

    mapped_scale = st.sidebar.slider(
        "Mapped count scale",
        min_value=0.0,
        max_value=1.2,
        value=1.0,
        step=0.05,
    )

    edge_scale = st.sidebar.slider(
        "Edge count scale",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
    )

    show_virtual = st.sidebar.checkbox("Show virtual entity", value=True)

    adjusted_entities = []
    for item in stats["entity_stats"]:
        row = copy.deepcopy(item)

        if row.get("input_source") == "virtual":
            if show_virtual:
                adjusted_entities.append(row)
            continue

        input_count = int(row.get("input_feature_count", 0) or 0)
        mapped_count = int(row.get("mapped_count", 0) or 0)
        new_mapped_count = min(int(round(mapped_count * mapped_scale)), input_count)
        row["mapped_count"] = new_mapped_count
        adjusted_entities.append(row)

    stats["entity_stats"] = adjusted_entities
    stats["entity_count"] = len(adjusted_entities)

    original_edge_counts = stats["edge_type_counts"]
    stats["edge_type_counts"] = {
        edge_type: int(round(count * edge_scale))
        for edge_type, count in original_edge_counts.items()
    }

    return status


def main():
    st.set_page_config(
        page_title="Processing Summary Preview",
        page_icon="📊",
        layout="wide",
    )

    st.title("Processing Summary Preview")
    st.caption("Preview page for frontend.components.processing_summary.render_processing_summary")

    status = build_adjusted_status()

    render_processing_summary(status)

    with st.expander("View mock status JSON"):
        st.json(status)


if __name__ == "__main__":
    main()