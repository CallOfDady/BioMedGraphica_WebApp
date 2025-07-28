# backend/service/processing_runner.py

from celery import chain, chord, group
from backend.tasks.steps import (
    compute_common_id_task,
    launch_processing_chord
)
from backend.service.task_tracker import update_task_status


def run_pipeline(config: dict):
    entities_cfgs = config["entities_cfgs"]
    label_cfg = config.get("label_cfg")
    finalize_cfg = config.get("finalize", {})
    output_dir = config.get("output_dir", "")
    job_id = config.get("job_id", "job_x")
    task_id = config.get("task_id", "task_x")

    update_task_status(task_id, "submitted", {"message": "Pipeline received, preparing tasks."})

    return chain(
        compute_common_id_task.s(config["entities_cfgs"], config["job_id"]),
        launch_processing_chord.s(config)  # This will handle chord creation and execution
    ).delay()