from typing import List, Dict, Any, Optional
import streamlit as st

def _format_candidate_option(cand: Dict[str, Any]) -> Optional[str]:
    """
    Convert a FAISS matcher candidate dict into a selectbox display string.

    Expected candidate format:
    {
        "entity_id": str,
        "conn_id": str,
        "score": float,
        "best_alias": str,
        ...
    }
    """
    if not isinstance(cand, dict):
        return None

    conn_id = str(cand.get("conn_id", "")).strip()
    if not conn_id:
        return None

    best_alias = str(cand.get("best_alias", "")).strip()
    score = cand.get("score", None)

    alias_part = best_alias if best_alias else "(no alias)"
    score_part = ""
    if isinstance(score, (int, float)):
        score_part = f" | score={score:.4f}"

    return f"{conn_id} - {alias_part}{score_part}"


def render_mapping_selector(candidate_data: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    if not candidate_data:
        st.info("✅ No mappings required.")
        return None

    structured_mappings = []

    with st.form("mapping_form"):
        st.markdown("### 🔍 Soft Match Mapping Selection")
        st.markdown(
            "Please select the best matches for each original ID. "
            "Changes will only be processed when you click 'Confirm Mappings'."
        )

        tabs = st.tabs([f"{d['entity_type']}" for d in candidate_data])

        for i, data in enumerate(candidate_data):
            entity_type = data["entity_type"]
            feature_label = data["feature_label"]
            candidates_map = data.get("candidates", {}) or {}

            feature_mappings = []

            with tabs[i]:
                st.markdown(f"### 🧬 {entity_type} ({feature_label})")
                st.markdown("---")

                # Optional metadata display
                total_original_ids = data.get("total_original_ids")
                if total_original_ids is not None:
                    st.caption(f"Total original IDs: {total_original_ids}")

                for original_id, options in candidates_map.items():
                    select_key = f"{entity_type}_{feature_label}_{original_id}"

                    # options is expected to be a list[dict]
                    option_labels = []
                    option_lookup = {}  # display_text -> candidate_dict

                    if isinstance(options, list):
                        for cand in options:
                            display_text = _format_candidate_option(cand)
                            if not display_text:
                                continue
                            # If duplicate display text appears, keep the first one
                            if display_text not in option_lookup:
                                option_lookup[display_text] = cand
                                option_labels.append(display_text)

                    select_options = ["-- No Match --"] + option_labels

                    default_value = st.session_state.get(select_key, "-- No Match --")
                    index = select_options.index(default_value) if default_value in select_options else 0

                    selected = st.selectbox(
                        f"Select match for '{original_id}'",
                        options=select_options,
                        index=index,
                        key=select_key,
                        help=f"Choose the best match for original ID: {original_id}"
                    )

                    if selected != "-- No Match --":
                        selected_cand = option_lookup.get(selected, {})
                        selected_id = str(selected_cand.get("conn_id", "")).strip() or None
                        selected_label = str(selected_cand.get("best_alias", "")).strip() or None
                    else:
                        selected_id, selected_label = None, None

                    feature_mappings.append({
                        "original_id": original_id,
                        "selected_id": selected_id,
                        "selected_label": selected_label
                    })

            structured_mappings.append({
                "entity_type": entity_type,
                "feature_label": feature_label,
                "mappings": feature_mappings
            })

        confirm_clicked = st.form_submit_button("✅ Confirm Mappings", type="primary")

        if confirm_clicked:
            st.session_state["_confirmed_mappings"] = structured_mappings
            st.success("Mappings confirmed!")
            return structured_mappings

    return None

# Example structure of candidate_data
# Type: List[Dict[str, Any]]
# [
#   {
#     "feature_label": "phenotype",
#     "entity_type": "Phenotype",
#     "total_original_ids": 12,
#     "candidates": {
#       "bpmed": [
#         {
#           "entity_id": "BMGE_PH000123",
#           "conn_id": "BMGC_PH09760",
#           "score": 1.0,
#           "best_alias": "Blood pressure medication",
#           "best_alias_score": 1.0,
#           "hit_alias_count": 2,
#           "match_type": "exact_ci"
#         },
#         {
#           "entity_id": "BMGE_PH000456",
#           "conn_id": "BMGC_PH10857",
#           "score": 0.9234,
#           "best_alias": "Antihypertensive agent",
#           "best_alias_score": 0.9234,
#           "hit_alias_count": 1
#         }
#       ],
#       "height": [
#         {
#           "entity_id": "BMGE_PH000789",
#           "conn_id": "BMGC_PH06948",
#           "score": 0.8812,
#           "best_alias": "Body height",
#           "best_alias_score": 0.8812,
#           "hit_alias_count": 1
#         }
#       ]
#     }
#   },
#   {
#     "feature_label": "exposure",
#     "entity_type": "Exposure",
#     "total_original_ids": 10,
#     "candidates": {
#       "smoker": [
#         {
#           "entity_id": "BMGE_EP001001",
#           "conn_id": "BMGC_EP1003",
#           "score": 0.9541,
#           "best_alias": "Smoking exposure",
#           "best_alias_score": 0.9541,
#           "hit_alias_count": 3
#         },
#         {
#           "entity_id": "BMGE_EP001002",
#           "conn_id": "BMGC_EP0973",
#           "score": 0.8123,
#           "best_alias": "Air pollution exposure",
#           "best_alias_score": 0.8123,
#           "hit_alias_count": 1
#         }
#       ]
#     }
#   }
# ]

# Example structure of output
# Type: List[Dict[str, Any]]
# [
#   {
#     "entity_type": "Phenotype",
#     "feature_label": "phenotype",
#     "mappings": [
#       {
#         "original_id": "bpmed",
#         "selected_id": "BMGC_PH09760",
#         "selected_label": "Blood pressure medication"
#       },
#       {
#         "original_id": "antideprmed",
#         "selected_id": None,
#         "selected_label": None
#       }
#     ]
#   }
# ]