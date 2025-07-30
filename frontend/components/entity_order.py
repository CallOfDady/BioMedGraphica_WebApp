import streamlit as st
from typing import List
from streamlit_sortables import sort_items
from frontend.components.log_console import log_to_console

def render_entity_order(
    entities: List[dict], 
    session_key: str = "file_order", 
    feature_key: str = "feature_label",
    log: bool = True
) -> List[str]:

    # Retrieve current order from session_state
    current_file_order = st.session_state.get(session_key, [])

    # Extract entity labels from the provided entities
    current_entities = [ent[feature_key] for ent in entities if ent.get(feature_key, "").strip()]

    # Sync file_order with the entities (add/remove if changed)
    if set(current_file_order) != set(current_entities):
        updated_order = [label for label in current_file_order if label in current_entities]
        new_entities = [label for label in current_entities if label not in updated_order]
        updated_order.extend(new_entities)
        st.session_state[session_key] = updated_order
        current_file_order = updated_order

        # Log syncing if needed
        if log:
            log_to_console(f"🔄 Entity order synced: {' → '.join(updated_order)}")

    if current_file_order:
        st.markdown(
            "<span style='font-size:14px;'>Drag to reorder entities.</span>",
            unsafe_allow_html=True
        )

        # Generate a unique key for the draggable list to avoid caching issues
        entity_hash = hash(tuple(current_file_order))
        sortable_key = f"entity_order_sortable_{entity_hash}"

        sorted_items = sort_items(current_file_order, key=sortable_key)

        # If order changed, update session_state and rerun
        if sorted_items != current_file_order:
            st.session_state[session_key] = sorted_items
            if log:
                log_to_console(f"📋 Entity order updated: {' → '.join(sorted_items)}")
            st.rerun()

        # Show current order visually
        st.caption(f"Current order:\n{' → '.join(current_file_order)}")

    else:
        st.info("Entity order will be generated automatically based on your selected entities.")

    return st.session_state.get(session_key, [])
