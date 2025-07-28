# backend/service/task_tracker.py

import redis
import json
import os

# Connect to Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def store_task_status(task_id: str, status: dict):
    r.set(f"task:{task_id}", json.dumps(status))

def get_task_status(task_id: str):
    val = r.get(f"task:{task_id}")
    return json.loads(val) if val else None

def update_task_status(task_id: str, status: str, update: dict = {}):
    current = get_task_status(task_id) or {}
    current.update(update)
    current["status"] = status
    store_task_status(task_id, current)