# backend/tasks/pipeline.py

from backend.celery_worker import celery_app
from backend.service.processing_runner import run_pipeline
from backend.service.task_tracker import update_task_status

@celery_app.task
def submit_processing_task(config: dict):
    task_id = config.get("task_id", "unknown")
    update_task_status(task_id, "submitted", {"message": "Pipeline received, preparing tasks."})

    # Launch pipeline
    result = run_pipeline(config)

    update_task_status(task_id, "queued", {"message": "Tasks enqueued."})

    return {"submitted": True, "task_id": task_id, "celery_id": result.id}