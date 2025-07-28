# backend/tasks/debug.py
from backend.celery_worker import celery_app

@celery_app.task
def debug_task():
    print("✅ Debug task ran")
    return "hello"