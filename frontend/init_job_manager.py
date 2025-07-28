# frontend/init_job_manager.py
import os
import streamlit as st
from pathlib import Path
from frontend.utils.job_manager import get_job_manager

def initialize_job_manager():
    """Initialize Streamlit front-end app with directories and temp manager"""
    if not st.session_state.get("_init_logged", False):
        print("Initializing BioMedGraphica UI...")


    job_manager = get_job_manager()
    job_id = job_manager.get_job_id()


    if not st.session_state.get("_init_logged", False):
        print(f"Temp directory ready: {job_manager.temp_root}")
        print(f"Job ID initialized: {job_id}")
        print("UI initialization complete")
        st.session_state["_init_logged"] = True

    # Create data_output directory under temp job directory
    job_dir = job_manager.get_job_dir()
    job_data_output_dir = job_dir / "data_output"
    job_data_output_dir.mkdir(parents=True, exist_ok=True)

    return job_manager, job_id, str(job_data_output_dir)

    # # Create cache directory if it doesn't exist
    # project_root = Path(".")
    # cache_dir = project_root / "cache"
    # cache_dir.mkdir(exist_ok=True)
    # print(f"Cache directory ready: {cache_dir}")

    # # Create processed_data directory within cache
    # processed_dir = cache_dir / "processed_data"
    # processed_dir.mkdir(exist_ok=True)
    # print(f"Processed data directory ready: {processed_dir}")

    # Init Job Manager (creates temp/)