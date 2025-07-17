"""
Temporary file management system for BioMedGraphica
Supports multi-user, multi-task file handling with automatic cleanup
"""

import os
import shutil
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import streamlit as st
import threading
import atexit


class TempFileManager:
    """Manages temporary files for multi-user, multi-task environment"""
    
    def __init__(self, project_root: str = ".", temp_dir: str = "temp", cleanup_interval_minutes: int = 10, auto_cleanup_on_startup: bool = True):
        self.project_root = Path(project_root)
        self.temp_dir = self.project_root / temp_dir
        self.cleanup_interval_minutes = cleanup_interval_minutes
        self._cleanup_started = False
        
        # Setup temp directory
        if auto_cleanup_on_startup:
            self._setup_temp_dir()
        else:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            print(f"Temp directory ready: {self.temp_dir}")
        
        # Start cleanup thread (only once globally)
        global _cleanup_started
        if not _cleanup_started:
            self._start_cleanup_thread()
        
        # Register cleanup on exit
        atexit.register(self.cleanup_on_exit)
    
    def _setup_temp_dir(self):
        """Setup temp directory and clean it on startup"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f" Cleaned up temp directory on startup: {self.temp_dir}")
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            print(f"Temp directory initialized: {self.temp_dir}")
        except Exception as e:
            print(f"Error setting up temp directory: {e}")
    
    def get_session_job_dir(self, create_if_not_exists: bool = True) -> Path:
        """Get or create job directory for current session"""
        # Use Streamlit session state to maintain job directory across reruns
        if "job_id" not in st.session_state:
            timestamp = datetime.now().strftime("%Y%m%d_%Hh%Mm%Ss")
            session_uuid = str(uuid.uuid4())[:8]
            st.session_state.job_id = f"job_{timestamp}_{session_uuid}"
            st.session_state.job_created_at = time.time()
        
        job_dir = self.temp_dir / st.session_state.job_id
        
        # Create directory by default for new sessions
        if create_if_not_exists and not job_dir.exists():
            job_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created job directory: {job_dir}")
        
        return job_dir
    
    def save_uploaded_file(self, uploaded_file, entity_label: str) -> str:
        """Save uploaded file to current session's job directory"""
        if uploaded_file is None:
            return ""
        
        # Create job directory only when actually uploading files
        job_dir = self.get_session_job_dir(create_if_not_exists=True)
        
        # Create filename based on entity label and original extension
        original_name = uploaded_file.name
        file_extension = Path(original_name).suffix
        safe_filename = f"{entity_label}{file_extension}"
        
        file_path = job_dir / safe_filename
        
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            print(f"Saved file: {safe_filename} to {job_dir}")
            return str(file_path)
        except Exception as e:
            print(f"Error saving file {safe_filename}: {e}")
            return ""
    
    def save_label_file(self, uploaded_file) -> str:
        """Save label file to current session's job directory"""
        if uploaded_file is None:
            return ""
        
        # Create job directory only when actually uploading files
        job_dir = self.get_session_job_dir(create_if_not_exists=True)
        
        # Keep original filename for label file
        original_name = uploaded_file.name
        file_path = job_dir / original_name
        
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            print(f"Saved label file: {original_name} to {job_dir}")
            return str(file_path)
        except Exception as e:
            print(f"Error saving label file {original_name}: {e}")
            return ""
    
    def get_current_job_info(self) -> Dict[str, Any]:
        """Get current job information and ensure job directory exists"""
        # Create job directory for current session (this ensures every session gets a temp folder)
        job_dir = self.get_session_job_dir(create_if_not_exists=True)
        created_at = st.session_state.get("job_created_at", time.time())
        
        return {
            "job_id": st.session_state.job_id,
            "job_dir": str(job_dir),
            "created_at": datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M:%S"),
            "age_minutes": (time.time() - created_at) / 60,
            "files": list(job_dir.glob("*")) if job_dir.exists() else []
        }
    
    def _cleanup_old_jobs(self):
        """Clean up old job directories"""
        try:
            if not self.temp_dir.exists():
                return
            
            current_time = time.time()
            cutoff_time = current_time - (self.cleanup_interval_minutes * 60)
            
            for job_dir in self.temp_dir.iterdir():
                if not job_dir.is_dir() or not job_dir.name.startswith("job_"):
                    continue
                
                try:
                    # Get job creation time from directory modification time
                    dir_mtime = job_dir.stat().st_mtime
                    
                    if dir_mtime < cutoff_time:
                        shutil.rmtree(job_dir)
                        print(f"Cleaned up old job directory: {job_dir.name}")
                except Exception as e:
                    print(f"Error cleaning up {job_dir.name}: {e}")
        
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        # Check if cleanup thread is already running globally
        global _cleanup_started, _cleanup_thread
        
        if _cleanup_started and _cleanup_thread is not None and _cleanup_thread.is_alive():
            print(f"Global cleanup thread already running")
            return
        
        def cleanup_worker():
            print(f"Global cleanup worker started (interval: {self.cleanup_interval_minutes} minutes)")
            while True:
                try:
                    time.sleep(self.cleanup_interval_minutes * 60)  # Sleep for cleanup interval
                    print(f"Running scheduled cleanup...")
                    # Get the current temp manager instance for cleanup
                    current_manager = get_temp_manager()
                    current_manager._cleanup_old_jobs()
                except Exception as e:
                    print(f"Error in cleanup thread: {e}")
        
        _cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        _cleanup_thread.start()
        _cleanup_started = True
        self._cleanup_started = True
        print(f"Started global cleanup thread (interval: {self.cleanup_interval_minutes} minutes)")
    
    def get_cleanup_thread_status(self) -> Dict[str, Any]:
        """Get status of cleanup thread"""
        global _cleanup_started, _cleanup_thread
        return {
            "thread_started": _cleanup_started,
            "thread_alive": _cleanup_thread.is_alive() if _cleanup_thread else False,
            "thread_name": _cleanup_thread.name if _cleanup_thread else None,
            "cleanup_interval_minutes": self.cleanup_interval_minutes,
            "temp_dir": str(self.temp_dir),
            "temp_dir_exists": self.temp_dir.exists()
        }
    

    def cleanup_on_exit(self):
        """Clean up on application exit"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f"Cleaned up temp directory on exit: {self.temp_dir}")
        except Exception as e:
            print(f"Error during exit cleanup: {e}")
    
    def force_cleanup_all(self):
        """Force cleanup of all temporary files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f"Force cleaned up all temp files")
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error during force cleanup: {e}")
    
    def get_temp_stats(self) -> Dict[str, Any]:
        """Get statistics about temporary files"""
        stats = {
            "total_jobs": 0,
            "total_files": 0,
            "total_size_mb": 0,
            "jobs": []
        }
        
        try:
            if not self.temp_dir.exists():
                return stats
            
            for job_dir in self.temp_dir.iterdir():
                if not job_dir.is_dir() or not job_dir.name.startswith("job_"):
                    continue
                
                stats["total_jobs"] += 1
                job_files = list(job_dir.glob("*"))
                stats["total_files"] += len(job_files)
                
                job_size = sum(f.stat().st_size for f in job_files if f.is_file())
                stats["total_size_mb"] += job_size / (1024 * 1024)
                
                job_created = datetime.fromtimestamp(job_dir.stat().st_mtime)
                stats["jobs"].append({
                    "name": job_dir.name,
                    "created": job_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "age_minutes": (time.time() - job_dir.stat().st_mtime) / 60,
                    "files": len(job_files),
                    "size_mb": job_size / (1024 * 1024)
                })
        
        except Exception as e:
            print(f"Error getting temp stats: {e}")
        
        return stats
    
    def delete_uploaded_file(self, entity_label: str) -> bool:
        """Delete uploaded file for a specific entity"""
        try:
            if "job_id" not in st.session_state:
                return False
            
            job_dir = self.get_session_job_dir(create_if_not_exists=False)
            
            # Only proceed if job directory exists
            if not job_dir.exists():
                return False
            
            # Try to find file by entity label with different extensions
            extensions = ['.csv', '.tsv', '.txt']
            deleted = False
            
            for ext in extensions:
                file_path = job_dir / f"{entity_label}{ext}"
                if file_path.exists():
                    file_path.unlink()
                    print(f"Deleted file: {file_path.name}")
                    deleted = True
            
            return deleted
        except Exception as e:
            print(f"Error deleting file for {entity_label}: {e}")
            return False

    def delete_label_file(self, filename: str) -> bool:
        """Delete label file by filename"""
        try:
            if "job_id" not in st.session_state:
                return False
            
            job_dir = self.get_session_job_dir(create_if_not_exists=False)
            
            # Only proceed if job directory exists
            if not job_dir.exists():
                return False
                
            file_path = job_dir / filename
            
            if file_path.exists():
                file_path.unlink()
                print(f"Deleted label file: {filename}")
                return True
            return False
        except Exception as e:
            print(f"Error deleting label file {filename}: {e}")
            return False
    
    def handle_file_upload_change(self, uploaded_file, entity_label: str, previous_file_key: str) -> str:
        """
        Handle file upload changes and automatically clean up when uploader is cleared
        
        Args:
            uploaded_file: Current uploaded file (None if cleared)
            entity_label: Entity label for the file
            previous_file_key: Session state key to track previous file state
            
        Returns:
            File path if file was uploaded, empty string otherwise
        """
        # Get previous file state
        had_file_before = st.session_state.get(previous_file_key, False)
        
        # Track if we had a file in the last run
        last_run_key = f"{previous_file_key}_last_run"
        had_file_last_run = st.session_state.get(last_run_key, False)
        
        if uploaded_file is not None:
            # File was uploaded
            st.session_state[previous_file_key] = True
            st.session_state[last_run_key] = True
            return self.save_uploaded_file(uploaded_file, entity_label)
        else:
            # File uploader is None - need to distinguish between page refresh and user clearing
            if had_file_before:
                # Check if the file still exists on disk
                job_dir = self.get_session_job_dir(create_if_not_exists=False)
                if job_dir.exists():
                    # Try to find existing file with different extensions
                    extensions = ['.csv', '.tsv', '.txt']
                    for ext in extensions:
                        file_path = job_dir / f"{entity_label}{ext}"
                        if file_path.exists():
                            # File exists on disk
                            if had_file_last_run:
                                # We had a file in the last run, but now uploader is None
                                # This means user clicked X button to clear it
                                self.delete_uploaded_file(entity_label)
                                print(f"Auto-deleted file for entity '{entity_label}' (user cleared uploader)")
                                st.session_state[previous_file_key] = False
                                st.session_state[last_run_key] = False
                                return ""
                            else:
                                # This is likely a page refresh - preserve the file
                                print(f"Page refresh detected - preserving existing file for entity '{entity_label}'")
                                st.session_state[last_run_key] = False
                                return str(file_path)
                    
                    # No file found on disk
                    if had_file_last_run:
                        print(f"File for entity '{entity_label}' was cleared by user")
                    st.session_state[previous_file_key] = False
                    st.session_state[last_run_key] = False
                    return ""
            
            # No file before
            st.session_state[previous_file_key] = False
            st.session_state[last_run_key] = False
            return ""
    
    def handle_label_file_change(self, uploaded_file, previous_file_key: str, previous_filename_key: str) -> str:
        """
        Handle label file upload changes and automatically clean up when uploader is cleared
        
        Args:
            uploaded_file: Current uploaded file (None if cleared)
            previous_file_key: Session state key to track previous file state
            previous_filename_key: Session state key to track previous filename
            
        Returns:
            File path if file was uploaded, empty string otherwise
        """
        # Get previous file state
        had_file_before = st.session_state.get(previous_file_key, False)
        previous_filename = st.session_state.get(previous_filename_key, "")
        
        # Track if we had a file in the last run
        last_run_key = f"{previous_file_key}_last_run"
        had_file_last_run = st.session_state.get(last_run_key, False)
        
        if uploaded_file is not None:
            # File was uploaded - check if it's a different file
            if previous_filename and previous_filename != uploaded_file.name:
                # User uploaded a different file - clean up the old one
                self.delete_label_file(previous_filename)
                print(f"Replaced label file: '{previous_filename}' → '{uploaded_file.name}'")
            
            st.session_state[previous_file_key] = True
            st.session_state[previous_filename_key] = uploaded_file.name
            st.session_state[last_run_key] = True
            return self.save_label_file(uploaded_file)
        else:
            # File uploader is None - need to distinguish between page refresh and user clearing
            if had_file_before and previous_filename:
                # Check if the file still exists on disk
                job_dir = self.get_session_job_dir(create_if_not_exists=False)
                if job_dir.exists():
                    file_path = job_dir / previous_filename
                    if file_path.exists():
                        # File exists on disk
                        if had_file_last_run:
                            # We had a file in the last run, but now uploader is None
                            # This means user clicked X button to clear it
                            self.delete_label_file(previous_filename)
                            print(f"Auto-deleted label file '{previous_filename}' (user cleared uploader)")
                            st.session_state[previous_file_key] = False
                            st.session_state[previous_filename_key] = ""
                            st.session_state[last_run_key] = False
                            return ""
                        else:
                            # This is likely a page refresh - preserve the file
                            print(f"Page refresh detected - preserving existing label file: '{previous_filename}'")
                            st.session_state[last_run_key] = False
                            return str(file_path)
                    else:
                        # File doesn't exist on disk anymore
                        print(f"Label file '{previous_filename}' was already removed")
                        st.session_state[previous_file_key] = False
                        st.session_state[previous_filename_key] = ""
                        st.session_state[last_run_key] = False
                        return ""
            
            # No file before or no previous filename
            st.session_state[previous_file_key] = False
            st.session_state[previous_filename_key] = ""
            st.session_state[last_run_key] = False
            return ""


# Global instance management
_temp_manager = None
_cleanup_started = False
_cleanup_thread = None

def get_temp_manager() -> TempFileManager:
    """Get global temp file manager instance"""
    global _temp_manager, _cleanup_started
    if _temp_manager is None:
        # In Streamlit environment, don't auto-cleanup on startup to allow testing
        auto_cleanup = not hasattr(st, 'session_state') or 'job_id' not in st.session_state
        _temp_manager = TempFileManager(auto_cleanup_on_startup=auto_cleanup)
        _cleanup_started = True
    return _temp_manager

def reset_temp_manager():
    """Reset the global temp manager (for testing)"""
    global _temp_manager, _cleanup_started, _cleanup_thread
    _temp_manager = None
    _cleanup_started = False
    _cleanup_thread = None
