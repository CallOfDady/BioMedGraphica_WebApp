# components/log_console.py


import streamlit as st

def log_to_console(message: str):
    logs = st.session_state.get("log_messages", [])
    logs.append(message)
    st.session_state["log_messages"] = logs


def render_log_console():
    st.markdown("### 📟 Processing Console")

    logs = st.session_state.get("log_messages", [])

    # Fixed height container for logs
    with st.container(height=300):
        st.markdown("""
        <style>
        .stChatMessage {
            padding-top: 0.2rem;
            padding-bottom: 0.2rem;
        }
        </style>
        """, unsafe_allow_html=True)

        for log in logs:
            with st.chat_message("log", avatar="🖥️"):
                st.markdown(log)