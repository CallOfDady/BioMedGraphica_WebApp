import altair as alt
import pandas as pd
import streamlit as st


LEFT_PANEL_HEIGHT = 720
RIGHT_PANEL_HEIGHT = 720
RIGHT_SECTION_HEIGHT = 350
ROW_HEIGHT = 36


def _safe_recall(mapped_count, input_feature_count):
    if input_feature_count in (None, 0):
        return None
    return float(mapped_count or 0) / float(input_feature_count) * 100.0


def _build_summary_df(stats, entity_stats):
    file_entities = [item for item in entity_stats if item.get("input_source", "file") == "file"]
    total_input = sum(int(item.get("input_feature_count", 0) or 0) for item in file_entities)
    total_mapped = sum(int(item.get("mapped_count", 0) or 0) for item in file_entities)
    overall_recall = _safe_recall(total_mapped, total_input)

    return pd.DataFrame([
        {
            "Metric": "Overall Recall",
            "Value": f"{overall_recall:.2f}%" if overall_recall is not None else "N/A",
        },
        {"Metric": "Total samples", "Value": stats.get("sample_count", 0)},
        {"Metric": "Selected edges", "Value": stats.get("total_selected_edges", 0)},
        {"Metric": "Entity Types", "Value": stats.get("entity_count", len(entity_stats))},
    ])


def _build_entity_table_df(entity_stats):
    rows = []
    for item in entity_stats:
        source = item.get("input_source", "file")
        recall = None if source == "virtual" else _safe_recall(
            item.get("mapped_count", 0),
            item.get("input_feature_count", 0),
        )
        rows.append({
            "Entity Label": item.get("feature_label", ""),
            "Entity Type": item.get("entity_type", ""),
            "Source": source,
            "Recall": "N/A" if recall is None else f"{recall:.2f}%",
        })

    return pd.DataFrame(rows)


def _build_entity_chart_df(entity_stats):
    rows = []
    for item in entity_stats:
        source = item.get("input_source", "file")
        recall = None if source == "virtual" else _safe_recall(
            item.get("mapped_count", 0),
            item.get("input_feature_count", 0),
        )
        rows.append({
            "Entity Label": item.get("feature_label", ""),
            "Entity Type": item.get("entity_type", ""),
            "Source": source,
            "Input Total": int(item.get("input_feature_count", 0) or 0),
            "Mapped": int(item.get("mapped_count", 0) or 0),
            "Recall Value": 0 if recall is None else recall,
            "Recall": "N/A" if recall is None else f"{recall:.2f}%",
            "Is Virtual": source == "virtual",
        })

    chart_df = pd.DataFrame(rows)
    if chart_df.empty:
        return chart_df

    return chart_df.sort_values(
        by=["Is Virtual", "Recall Value", "Entity Label"],
        ascending=[True, False, True],
    )


def _build_edge_table_df(edge_type_counts):
    return pd.DataFrame(
        [
            {
                "Edge Type": edge_type,
                "Count": count,
                "Count Plot": max(int(count), 1),
                "Count Label": _format_compact_number(count),
                "Count Exact": f"{int(count):,}",
            }
            for edge_type, count in edge_type_counts.items()
        ]
    ).sort_values(by=["Count", "Edge Type"], ascending=[False, True])


def _format_compact_number(value):
    value = float(value or 0)
    abs_value = abs(value)

    if abs_value >= 1_000_000:
        formatted = f"{value / 1_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{formatted}M"
    if abs_value >= 1_000:
        formatted = f"{value / 1_000:.1f}".rstrip("0").rstrip(".")
        return f"{formatted}k"
    return str(int(value))


def _build_log_tick_values(max_count):
    tick_values = []
    value = 1

    while value <= max(max_count, 1):
        tick_values.append(value)
        value *= 100

    if tick_values[-1] < max_count:
        tick_values.append(value)

    return tick_values


def _build_entity_recall_chart(entity_chart_df):
    if entity_chart_df.empty:
        st.info("No entity recall data available.")
        return

    chart_height = max(260, len(entity_chart_df) * ROW_HEIGHT)
    base = alt.Chart(entity_chart_df).encode(
        y=alt.Y(
            "Entity Label:N",
            sort=entity_chart_df["Entity Label"].tolist(),
            title="Entity",
        )
    )

    bars = base.mark_bar().encode(
        x=alt.X("Recall Value:Q", title="Recall (%)", scale=alt.Scale(domain=[0, 100])),
        color=alt.condition(
            alt.datum["Is Virtual"],
            alt.value("#c7c7c7"),
            alt.value("#4c956c"),
        ),
        tooltip=[
            alt.Tooltip("Entity Label:N"),
            alt.Tooltip("Entity Type:N"),
            alt.Tooltip("Source:N"),
            alt.Tooltip("Input Total:Q", format=",", title="Input Total"),
            alt.Tooltip("Mapped:Q", format=",", title="Mapped"),
            alt.Tooltip("Recall:N"),
        ],
    )

    labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=6,
        color="#2f2f2f",
        tooltip=False,
    ).encode(
        x=alt.X("Recall Value:Q"),
        text="Recall:N",
    )

    chart = (
        (bars + labels)
        .properties(height=chart_height)
        .configure_axis(labelLimit=220)
    )
    st.altair_chart(chart, use_container_width=True)


def _build_edge_count_chart(edge_df):
    if edge_df.empty:
        st.info("No edge count data available.")
        return

    chart_height = max(260, len(edge_df) * ROW_HEIGHT)
    log_tick_values = _build_log_tick_values(int(edge_df["Count Plot"].max()))
    base = alt.Chart(edge_df).encode(
        y=alt.Y(
            "Edge Type:N",
            sort=edge_df["Edge Type"].tolist(),
            title="Edge Type",
        )
    )

    bars = base.mark_bar(color="#3d5a80").encode(
        x=alt.X(
            "Count Plot:Q",
            title="Count (log scale)",
            scale=alt.Scale(type="log", domainMin=1),
            axis=alt.Axis(format="~s", values=log_tick_values),
        ),
        x2=alt.X2(datum=1),
        tooltip=[
            alt.Tooltip("Edge Type:N"),
            alt.Tooltip("Count Exact:N", title="Count"),
        ],
    )

    labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=6,
        color="#2f2f2f",
        tooltip=False,
    ).encode(
        x=alt.X("Count Plot:Q"),
        text="Count Label:N",
    )

    chart = (
        (bars + labels)
        .properties(height=chart_height, padding={"right": 36})
        .configure_axis(labelLimit=220)
    )
    st.altair_chart(chart, use_container_width=True)


def render_processing_summary(status):
    result = status.get("result") or {}
    stats = result.get("stats") or {}
    entity_stats = stats.get("entity_stats") or []
    edge_type_counts = stats.get("edge_type_counts") or {}

    summary_df = _build_summary_df(stats, entity_stats)
    entity_df = _build_entity_table_df(entity_stats)
    entity_chart_df = _build_entity_chart_df(entity_stats)
    edge_df = _build_edge_table_df(edge_type_counts) if edge_type_counts else pd.DataFrame(columns=["Edge Type", "Count"])

    left_col, right_col = st.columns([5, 4], gap="large")

    with left_col:
        with st.container(border=True, height=LEFT_PANEL_HEIGHT):
            st.markdown("#### Processing Summary")
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            st.markdown("#### Entity Matching Breakdown")
            st.dataframe(entity_df, use_container_width=True, hide_index=True)

    with right_col:
        with st.container(border=True, height=RIGHT_PANEL_HEIGHT):
            with st.container(height=RIGHT_SECTION_HEIGHT):
                st.markdown("#### Entity Matching Recall")
                _build_entity_recall_chart(entity_chart_df)

            with st.container(height=RIGHT_SECTION_HEIGHT):
                st.markdown("#### Edge Type Count")
                _build_edge_count_chart(edge_df)
