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
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return str(file_path)

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
        had_file_before = st.session_state.get(previous_file_key, False)
        had_file_last_run = st.session_state.get(last_run_key, False)

        if uploaded_file is not None:
            st.session_state[previous_file_key] = True
            st.session_state[last_run_key] = True
            return self.save_uploaded_entity_file(uploaded_file, entity_label)
        else:
            if had_file_before:
                job_dir = self.get_job_dir()
                for ext in ['.csv', '.tsv', '.txt']:
                    file_path = job_dir / f"{entity_label}{ext}"
                    if file_path.exists():
                        if had_file_last_run:
                            self.delete_uploaded_entity_file(entity_label)
                            st.session_state[previous_file_key] = False
                            st.session_state[last_run_key] = False
                            return ""
                        else:
                            st.session_state[last_run_key] = False
                            return str(file_path)
                st.session_state[previous_file_key] = False
                st.session_state[last_run_key] = False
                return ""
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

            print(f"Saved label file: {uploaded_file.name} to {job_dir}")
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
        had_file_before = st.session_state.get(previous_file_key, False)
        previous_filename = st.session_state.get(previous_filename_key, "")
        last_run_key = f"{previous_file_key}_last_run"
        had_file_last_run = st.session_state.get(last_run_key, False)

        if uploaded_file is not None:
            # User uploaded a new file
            if previous_filename and previous_filename != uploaded_file.name:
                self.delete_uploaded_label_file(previous_filename)
                print(f"Replaced label file: '{previous_filename}' → '{uploaded_file.name}'")

            st.session_state[previous_file_key] = True
            st.session_state[previous_filename_key] = uploaded_file.name
            st.session_state[last_run_key] = True
            return self.save_uploaded_label_file(uploaded_file)

        # File uploader is cleared
        if had_file_before and previous_filename:
            job_dir = self.get_job_dir()
            file_path = job_dir / previous_filename
            if file_path.exists():
                if had_file_last_run:
                    self.delete_uploaded_label_file(previous_filename)
                    print(f"Auto-deleted label file '{previous_filename}' (user cleared uploader)")
                    st.session_state[previous_file_key] = False
                    st.session_state[previous_filename_key] = ""
                    st.session_state[last_run_key] = False
                    return ""
                else:
                    # Refresh scenario
                    print(f"Page refresh - preserving label file: {previous_filename}")
                    st.session_state[last_run_key] = False
                    return str(file_path)

            # File no longer exists
            print(f"Label file '{previous_filename}' was already removed")
            st.session_state[previous_file_key] = False
            st.session_state[previous_filename_key] = ""
            st.session_state[last_run_key] = False
            return ""

        # No file previously
        st.session_state[previous_file_key] = False
        st.session_state[previous_filename_key] = ""
        st.session_state[last_run_key] = False
        return ""

# global singleton
_job_manager = None

def get_job_manager() -> JobManager:
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager