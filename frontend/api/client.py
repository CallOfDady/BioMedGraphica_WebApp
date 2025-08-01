# frontend/api/client.py

from dotenv import load_dotenv
import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def submit_async_processing_task(payload: dict) -> str:
    """
    Call FastAPI backend to submit a processing job.
    """
    # print("Submitting payload to backend:", payload)
    url = f"{BACKEND_URL}/api/submit"
    response = requests.post(url, json=payload)
    response.raise_for_status()

    return response.json()["task_id"]

def submit_mappings_to_backend(task_id: str, mappings: dict):
    print("Submitting mappings to backend:", {"task_id": task_id, "mappings": mappings})
    response = requests.post(
        f"{BACKEND_URL}/api/submit-mappings",
        json={"task_id": task_id, "mappings": mappings}
    )
    response.raise_for_status()

def check_task_status(task_id: str) -> dict:
    """
    Query backend for current task status.
    """
    url = f"{BACKEND_URL}/api/status/{task_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def download_results(task_id: str) -> str:
    """
    Get download URL for completed task results.
    """
    return f"{BACKEND_URL}/api/download/{task_id}"

def check_backend_config():
    """Check backend configuration status."""
    response = requests.get(f"{BACKEND_URL}/api/config/status")
    return response.json()