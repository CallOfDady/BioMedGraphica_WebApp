from pathlib import Path
import shutil
import time
import uuid
from datetime import datetime
from typing import Dict, Any


class TempManager:
    """Temp manager with job_id support and no Streamlit dependency."""

    def __init__(self, base_dir: str = "temp"):
        self.temp_root = Path(base_dir)
        self.temp_root.mkdir(parents=True, exist_ok=True)

    def get_job_dir(self, job_id: str, create_if_missing: bool = True) -> Path:
        """Return the path to a specific job directory."""
        job_dir = self.temp_root / job_id
        if create_if_missing:
            job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    def save_file(self, job_id: str, filename: str, content: bytes) -> str:
        """Save a file into a specific job's folder."""
        job_dir = self.get_job_dir(job_id)
        file_path = job_dir / filename
        with open(file_path, "wb") as f:
            f.write(content)
        return str(file_path)

    def get_job_info(self, job_id: str) -> Dict[str, Any]:
        """Return metadata about the job."""
        job_dir = self.get_job_dir(job_id, create_if_missing=False)
        if not job_dir.exists():
            return {"exists": False}
        created_at = datetime.fromtimestamp(job_dir.stat().st_mtime)
        return {
            "job_id": job_id,
            "path": str(job_dir),
            "created_at": created_at.isoformat(),
            "files": [f.name for f in job_dir.glob("*")],
        }

    def delete_job(self, job_id: str) -> bool:
        """Delete a job folder and its contents."""
        job_dir = self.get_job_dir(job_id, create_if_missing=False)
        if job_dir.exists():
            shutil.rmtree(job_dir)
            return True
        return False

    def list_all_jobs(self) -> list:
        """List all job IDs in the temp folder."""
        return [d.name for d in self.temp_root.glob("job_*") if d.is_dir()]

    def get_job_age_seconds(self, job_id: str) -> float:
        """Return job age in seconds."""
        job_dir = self.get_job_dir(job_id, create_if_missing=False)
        if job_dir.exists():
            return time.time() - job_dir.stat().st_mtime
        return -1.0


def cleanup_old_jobs(temp_base: str = "temp", max_age_sec: int = 1800) -> int:
    """Standalone function to clean up expired job folders."""
    temp_path = Path(temp_base)
    now = time.time()
    count = 0

    for job_dir in temp_path.glob("job_*"):
        if not job_dir.is_dir():
            continue
        age = now - job_dir.stat().st_mtime
        if age > max_age_sec:
            shutil.rmtree(job_dir)
            count += 1

    return count