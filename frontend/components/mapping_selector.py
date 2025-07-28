from typing import List, Dict, Any, Optional
import streamlit as st

def render_mapping_selector(candidate_data: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    if not candidate_data:
        st.info("✅ No mappings required.")
        return None

    structured_mappings = []

    tabs = st.tabs([f"{d['entity_type']}" for d in candidate_data])

    for i, data in enumerate(candidate_data):
        entity_type = data["entity_type"]
        feature_label = data["feature_label"]
        candidates = data["candidates"]

        feature_mappings = []

        with tabs[i]:
            st.markdown(f"### 🧬 {entity_type}")
            for original_id, options in candidates.items():
                select_key = f"{entity_type}_{feature_label}_{original_id}"
                select_options = ["-- No Match --"] + [
                    f"{cand_id} - {desc}" for cand_id, desc in options
                ]

                default_value = st.session_state.get(select_key, "-- No Match --")
                index = select_options.index(default_value) if default_value in select_options else 0

                selected = st.selectbox(
                    f"🔗 Match for `{original_id}`",
                    options=select_options,
                    index=index,
                    key=select_key,
                    label_visibility="collapsed"
                )

                if selected != "-- No Match --":
                    selected_id, selected_label = selected.split(" - ", 1)
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

    # Button to confirm mappings
    if st.button("✅ Confirm Mappings", type="primary"):
        st.session_state["_confirmed_mappings"] = structured_mappings
        st.success("Mappings confirmed!")
        return structured_mappings

    return None

# # Example structure of candidate_data
# # Type: List[Dict[str, Any]]
# [
#   {
#     "feature_label": "phenotype",
#     "entity_type": "Phenotype",
#     "total_original_ids": 12,
#     "candidates": {
#       "bpmed": [
#         ["BMGC_PH09760", "Axial"],
#         ["BMGC_PH10857", "Central"],
#         ...
#       ],
#       "height": [
#         ["BMGC_PH06948", "Alexia"],
#         ["BMGC_PH09187", "Right"],
#         ...
#       ],
#       ...
#     }
#   },
#   {
#     "feature_label": "exposure",
#     "entity_type": "Exposure",
#     "total_original_ids": 10,
#     "candidates": {
#       "smoker": [
#         ["BMGC_EP1003", "Tobacco tar"],
#         ["BMGC_EP0973", "Smog"],
#         ...
#       ],
#       ...
#     }
#   }
# ]

# # Example structure of output
#  Type: List[Dict[str, Any]]
# [
#   {
#     "entity_type": "Phenotype",
#     "feature_label": "phenotype",
#     "mappings": [
#       {
#         "original_id": "bpmed",
#         "selected_id": "BMGC_PH09760",
#         "selected_label": "Axial"
#       },
#       {
#         "original_id": "antideprmed",
#         "selected_id": None,
#         "selected_label": None
#       }
#     ]
#   },
#   ...
# ]