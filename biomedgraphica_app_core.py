"""
biomedgraphica_core.py

"""

import json, uuid
from typing import Dict, List

from biomedgraphica_app_constants import (
    ENTITY_TYPES, ID_TYPES, DEFAULT_FILE_ORDER, DEFAULT_EDGE_TYPES
)
from components.entity_row import render_entity_row
from components.log_console import render_log_console, log_to_console

import streamlit as st


# --------------------------- HELPERS -------------------------------------

def _build_file_order(entities):
    return [e["feature_label"].strip() for e in entities if e["feature_label"].strip()] or DEFAULT_FILE_ORDER

def log_to_console(message: str):
    logs = st.session_state.get("log_messages", [])
    logs.append(message)
    st.session_state["log_messages"] = logs

# --------------------------- MAIN BUILDER --------------------------------

def build_app():

    # ---------- Session init ----------
    if "entities" not in st.session_state:
        st.session_state.entities = [dict(uuid=str(uuid.uuid4()), fill0=False, feature_label="", entity_type="", id_type=ID_TYPES[""][0], file_path="") for _ in range(4)]
    st.session_state.setdefault("label_path", "")
    st.session_state.setdefault("file_order", DEFAULT_FILE_ORDER.copy())
    st.session_state.setdefault("edge_types", DEFAULT_EDGE_TYPES.copy())
    st.session_state.setdefault("apply_zscore", False)
    st.session_state.setdefault("step1_open", True)
    st.session_state.setdefault("step2_open", False)

    st.session_state.setdefault("log_messages", ["📟 Processing console initialized."])

    # ---------- UI ----------
    st.set_page_config(f"BiomedGraphica Integration", layout="wide")
    st.title("🧬 BiomedGraphica – Data Integration")

    # ---------- Project Header ----------
    st.markdown("""
    **BioMedGraphica Data Integration App** is a Web-based GUI tool that enables researchers to convert biomedical data into structured graph-ready format for **AI in Precision Health and Medicine**.

    - Upload and align **multi-omics and clinical datasets**
    - Perform **entity recognition** via hard or soft matching
    - Construct **custom knowledge-signaling graphs**
    - Export **graph-ready `.npy` files** for downstream modeling
    """)


    st.divider()

    # Two main columns for the app
    main_left, main_right = st.columns([3, 2], gap="large")

    with main_left:

        # -------- Step 1 --------
        with st.expander("Step 1 – Entities & Labels", expanded=st.session_state.step1_open):
            st.subheader("Entities")

            # Entity rows (import from components/entity_row.py)
            remove_indices = []
            for i, ent in enumerate(st.session_state.entities):
                if render_entity_row(ent):
                    remove_indices.append(i)

            # Remove selected rows
            for i in sorted(remove_indices, reverse=True):
                del st.session_state.entities[i]
            if remove_indices:
                st.rerun()

            # Add button
            if st.button("➕ Add entity"):
                st.session_state.entities.append(dict(
                    uuid=str(uuid.uuid4()),
                    fill0=False,
                    feature_label="",
                    entity_type="",
                    id_type=ID_TYPES[""][0],
                    file_path=""
                ))
                st.rerun()

            st.markdown("---")
            st.subheader("Label")
            lup = st.file_uploader("Upload Label File", type=["csv", "tsv", "txt"], key="lbl_up", label_visibility="collapsed")
            if lup is not None:
                st.session_state.label_path = lup.name

            # Next button
            btn_l, btn_r = st.columns([1, 1])
            with btn_l:
                st.empty()
            with btn_r:
                if st.button("Next ➡", key="step1_next", use_container_width=True):
                    st.session_state.file_order = _build_file_order(st.session_state.entities)
                    st.session_state.step1_open, st.session_state.step2_open = False, True
                    st.rerun()

        # -------- Step 2 --------
        with st.expander("Step 2 – Finalise & Run", expanded=st.session_state.step2_open):
            l, r = st.columns(2)
            with l:
                fo = st.text_input("File order", ", ".join(st.session_state.file_order))
                st.session_state.file_order = [s.strip() for s in fo.split(',') if s.strip()]
                new_zscore = st.checkbox("Apply Z-score", value=st.session_state.apply_zscore, key="zscore_check")
                if new_zscore != st.session_state.apply_zscore:
                    st.session_state.apply_zscore = new_zscore
            with r:
                et = st.text_area("Edge types", "\n".join(st.session_state.edge_types), height=150)
                st.session_state.edge_types = [s.strip() for s in et.split('\n') if s.strip()]
            db = st.text_input("DB path", "E:/LabWork/BioMedGraphica-Conn")
            od = st.text_input("Output dir", "cache")

            # Back and Run buttons
            btn_l, btn_r = st.columns([1, 1])
            with btn_l:
                if st.button("⬅ Back", key="step2_back", use_container_width=True):
                    st.session_state.step1_open, st.session_state.step2_open = True, False
                    st.rerun()
            with btn_r:
                if st.button("▶️ Run processing", key="step2_run", use_container_width=True):
                    cfgs = [dict(feature_label=e["feature_label"], entity_type=e["entity_type"].lower(), id_type=e["id_type"], file_path=e["file_path"], fill0=e["fill0"]) for e in st.session_state.entities if e["feature_label"].strip()]
                    if st.session_state.label_path:
                        cfgs.append(dict(feature_label="label", entity_type="label", id_type="", file_path=st.session_state.label_path, fill0=False))
                    final = dict(
                        configs=cfgs,
                        finalize=dict(
                            file_order=st.session_state.file_order,
                            apply_zscore=st.session_state.apply_zscore,
                            edge_types=st.session_state.edge_types,
                        )
                    )
                    st.code(json.dumps(final, indent=2), language="json")
                    try:
                        from backend.processors import process
                        res = process(*final["configs"], database_path=db, output_dir=od, file_order=final["finalize"].get("file_order"), apply_zscore=final["finalize"].get("apply_zscore", False), edge_types=final["finalize"].get("edge_types"))
                        st.success(f"Done: {res['summary']['success']} / {res['summary']['total']}")
                    except Exception as exc:
                        st.exception(exc)

    with main_right:
        st.markdown("### 🕸️  Graph")
        st.info("placeholder placeholder placeholder placeholder placeholder placeholder")

        st.divider()

        # Status info box
        render_log_console()

    # ---------- style tweaks ----------
    st.markdown("""
    <style>
    section[data-testid='stFileUploader'] label div span {display:none!important;}
    button[kind='primary'] {width:100%}

    /* Disable text area resizing */
    textarea[data-testid="stTextArea"] {
        resize: none !important;
    }

    /* Add scrollbar style for status info box */
    div[data-testid="stTextArea"] textarea {
        resize: none !important;
        overflow-y: auto !important;
    }

    /* Set default state to red */
    button[data-testid="baseButton-primary"] {
        background-color: #ff4b4b !important;
        border-color: #ff4b4b !important;
    }

    /* Hover state to green */
    button[data-testid="baseButton-primary"]:hover {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
    }

    /* Remove extra styles for focus and active states */
    button[data-testid="baseButton-primary"]:focus,
    button[data-testid="baseButton-primary"]:active,
    button[data-testid="baseButton-primary"]:focus:not(:focus-visible) {
        outline: none !important;
        box-shadow: none !important;
        transform: none !important;
    }

    </style>""", unsafe_allow_html=True)