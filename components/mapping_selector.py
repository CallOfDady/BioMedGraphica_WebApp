# components/collapsible_mapping_selector.py

import streamlit as st
import streamlit_nested_layout
from typing import List, Tuple, Optional, Dict, Any
import pandas as pd

def render_collapsible_mapping_ui():

    if st.session_state.get("_just_confirmed_mappings", False):
        print(f"Mappings just confirmed - checking for additional pending mappings...")

    # Find all pending mapping sessions
    pending_sessions = {}
    for key in st.session_state.keys():
        if key.startswith("mapping_session_") and not key.endswith("_results"):
            session_data = st.session_state[key]
            # Only consider sessions that are not completed and have mapping data
            if not session_data.get("completed", False) and "mapping_data" in session_data:
                pending_sessions[key] = session_data
    
    # Debug: Print session state info
    print(f"Checking for pending mapping sessions...")
    print(f"  - Total session state keys: {len(st.session_state.keys())}")
    mapping_keys = [key for key in st.session_state.keys() if key.startswith("mapping_session_")]
    print(f"  - Mapping session keys found: {mapping_keys}")
    for key in mapping_keys:
        if not key.endswith("_results"):  # Skip results keys
            session_data = st.session_state[key]
            print(f"  - {key}: completed={session_data.get('completed', False)}, has_mapping_data={'mapping_data' in session_data}")
    print(f"  - Pending sessions: {len(pending_sessions)}")
    
    if not pending_sessions:
        print("   - No pending mappings found, returning False")
        return False  # No pending mappings
    
    # Show header and nested expander for ID mappings
    total_mappings = sum(len(session["mapping_data"]) for session in pending_sessions.values())
    
    print(f"  - Showing mapping UI for {len(pending_sessions)} sessions with {total_mappings} total mappings")
    
    # Use nested expander instead of checkbox
    with st.expander(f"🔗 ID Mapping Required ({len(pending_sessions)} entities, {total_mappings} mappings)", expanded=True):
        st.info("⏳ **Processing is paused. Please complete the mappings below and click 'Confirm All Mappings' to continue.**")
        
        # Process each pending session
        for session_key, session_data in pending_sessions.items():
            entity_type = session_data["entity_type"]
            feature_label = session_data["feature_label"]
            mapping_data = session_data["mapping_data"]
            
            st.subheader(f"📋 {entity_type}")
            
            # Render mapping selectors for this entity
            current_selections = render_entity_mapping_selectors(
                entity_type=entity_type,
                mapping_data=mapping_data,
                session_key=session_key
            )
            
            # Update session state with current selections
            results_key = f"{session_key}_results"
            st.session_state[results_key] = current_selections
            
            # Show mapping summary
            mapped_count = sum(1 for v in current_selections.values() if v is not None)
            st.caption(f"📊 Progress: {mapped_count}/{len(mapping_data)} mappings completed")
            
            st.divider()
        
        # Global action buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("❌ Cancel Processing", key="cancel_all_mappings", use_container_width=True):
                # Clear all pending sessions
                for session_key in list(pending_sessions.keys()):
                    if session_key in st.session_state:
                        del st.session_state[session_key]
                    
                    # Clear related keys
                    keys_to_remove = [key for key in st.session_state.keys() 
                                     if key.startswith(session_key)]
                    for key in keys_to_remove:
                        del st.session_state[key]
                
                st.warning("⚠️ Processing cancelled. All pending mappings have been cleared.")
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset All", key="reset_all_mappings", use_container_width=True):
                # Reset all pending sessions
                for session_key in pending_sessions.keys():
                    # Clear all selections
                    keys_to_remove = [key for key in st.session_state.keys() 
                                     if key.startswith(f"mapping_selector_{session_key}")]
                    for key in keys_to_remove:
                        del st.session_state[key]
                    
                    # Reset session data
                    st.session_state[session_key]["completed"] = False
                    st.session_state[session_key]["selections"] = {}
                    
                    # Clear results
                    results_key = f"{session_key}_results"
                    if results_key in st.session_state:
                        del st.session_state[results_key]
                
                st.info("🔄 All mappings have been reset.")
                st.rerun()
        
        with col3:
            if st.button("✅ Confirm All Mappings", key="confirm_all_mappings", use_container_width=True):
                # Confirm all pending sessions
                confirmed_any = False
                for session_key in pending_sessions.keys():
                    results_key = f"{session_key}_results"
                    if results_key in st.session_state:
                        current_selections = st.session_state[results_key]
                        # Mark session as completed
                        st.session_state[session_key]["selections"] = current_selections
                        st.session_state[session_key]["completed"] = True
                        confirmed_any = True
                
                if confirmed_any:
                    st.success("✅ All mappings confirmed! Processing will continue...")
                    # Set flag to trigger auto-processing and ensure it's processed in the next run
                    st.session_state["_just_confirmed_mappings"] = True
                    
                    st.rerun()
        
    return True  # Has pending mappings


def render_entity_mapping_selectors(
    entity_type: str,
    mapping_data: Dict[str, List[Tuple[str, str]]],
    session_key: str
) -> Dict[str, Optional[str]]:
    """
    Render mapping selectors for a specific entity type.
    
    Args:
        entity_type: Type of entity being mapped
        mapping_data: Dict mapping original_id to list of candidates
        session_key: Unique key for this mapping session
        
    Returns:
        Dict mapping original_id to selected BMG ID
    """
    current_selections = {}
    
    # Create a more compact layout
    for original_id, candidates in mapping_data.items():
        # Create a unique key for this selector
        selector_key = f"mapping_selector_{session_key}_{original_id}"
        
        if not candidates:
            st.warning(f"No candidates found for '{original_id}'")
            current_selections[original_id] = None
            continue
        
        # Create options for the selectbox
        options = ["-- No Match --"] + [f"{bmg_id} - {desc}" for bmg_id, desc in candidates]
        
        # Get current value from session state if it exists
        current_value = None
        if selector_key in st.session_state:
            current_value = st.session_state[selector_key]
        
        # Find the index of the current value in options
        index = 0
        if current_value and current_value in options:
            index = options.index(current_value)
        
        # Display the selector in a more compact format
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.text(f"'{original_id}'")
        
        with col2:
            selected_option = st.selectbox(
                f"Select mapping:",
                options,
                index=index,
                key=selector_key,
                help=f"Choose the best match for '{original_id}' from the top candidates.",
                label_visibility="collapsed"
            )
        
        # Store the selection
        if selected_option == "-- No Match --":
            current_selections[original_id] = None
        else:
            # Extract BMG ID from the selected option
            bmg_id = selected_option.split(" - ")[0]
            current_selections[original_id] = bmg_id
    
    return current_selections
