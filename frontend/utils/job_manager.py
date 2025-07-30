"""
Temp File Manager for UI (session-aware)
"""

import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import streamlit as st


class JobManager:
    def __init__(self, base_dir: str = "temp"):
        self.temp_root = Path(base_dir)
        self.temp_root.mkdir(parents=True, exist_ok=True)

    def get_job_id(self) -> str:
        if "job_id" not in st.session_state:
            timestamp = datetime.now().strftime("%Y%m%d_%Hh%Mm%Ss")
            session_uuid = str(uuid.uuid4())[:8]
            st.session_state.job_id = f"job_{timestamp}_{session_uuid}"
            st.session_state.job_created_at = time.time()
        return st.session_state.job_id

    def get_job_dir(self) -> Path:
        job_id = self.get_job_id()
        job_dir = self.temp_root / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    def get_job_info(self) -> Dict[str, Any]:
        job_dir = self.get_job_dir()
        created_at = st.session_state.get("job_created_at", time.time())
        return {
            "job_id": self.get_job_id(),
            "job_dir": str(job_dir),
            "created_at": datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M:%S"),
            "age_minutes": (time.time() - created_at) / 60,
            "files": list(job_dir.glob("*")) if job_dir.exists() else [],
        }

    def save_uploaded_entity_file(self, uploaded_file, entity_label: str) -> str:
        if uploaded_file is None:
            return ""
        job_dir = self.get_job_dir()
        ext = Path(uploaded_file.name).suffix
        filename = f"{entity_label}{ext}"
        file_path = job_dir / filename

        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            # print(f"Saved entity file: {filename} to {job_dir}")
            return str(file_path)
        except Exception as e:
            print(f"Error saving entity file {filename}: {e}")
            return ""

    def delete_uploaded_entity_file(self, entity_label: str) -> bool:
        job_dir = self.get_job_dir()
        deleted = False
        for ext in ['.csv', '.tsv', '.txt']:
            file_path = job_dir / f"{entity_label}{ext}"
            if file_path.exists():
                file_path.unlink()
                deleted = True
        return deleted

    def handle_entity_file_change(self, uploaded_file, entity_label: str, previous_file_key: str) -> str:
        last_run_key = f"{previous_file_key}_last_run"

        if uploaded_file is not None:
            saved_path = self.save_uploaded_entity_file(uploaded_file, entity_label)
            st.session_state[previous_file_key] = True
            st.session_state[last_run_key] = True
            return saved_path

        # No file previously
        st.session_state[previous_file_key] = False
        st.session_state[last_run_key] = False
        return ""

    def save_uploaded_label_file(self, uploaded_file) -> str:
        if uploaded_file is None:
            return ""
        
        # Save label file in the job directory
        job_dir = self.get_job_dir()
        file_path = job_dir / uploaded_file.name
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            # print(f"Saved label file: {uploaded_file.name} to {job_dir}")
            return str(file_path)
        except Exception as e:
            print(f"Error saving label file {uploaded_file.name}: {e}")
            return ""

    def delete_uploaded_label_file(self, filename: str) -> bool:
        job_dir = self.get_job_dir()
        file_path = job_dir / filename
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"Deleted label file: {filename}")
                return True
            except Exception as e:
                print(f"Error deleting label file {filename}: {e}")
        return False

    def handle_label_file_change(self, uploaded_file, previous_file_key: str, previous_filename_key: str) -> str:

        last_run_key = f"{previous_file_key}_last_run"

        # New upload
        if uploaded_file is not None:
            saved_path = self.save_uploaded_label_file(uploaded_file)
            st.session_state[previous_file_key] = True
            st.session_state[previous_filename_key] = uploaded_file.name
            st.session_state[last_run_key] = True
            st.session_state["_label_file_path"] = saved_path
            return saved_path

        # No file previously
        st.session_state[previous_file_key] = False
        st.session_state[previous_filename_key] = ""
        st.session_state[last_run_key] = False
        st.session_state["_label_file_path"] = ""
        return ""

# global singleton
_job_manager = None

def get_job_manager() -> JobManager:
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager