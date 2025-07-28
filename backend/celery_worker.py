# backend/celery_worker.py

from celery import Celery

celery_app = Celery(
    "biomedgraphica",
    broker="redis://localhost:6379/0", # Use Redis as the message broker
    backend="redis://localhost:6379/0" # Use Redis for result backend
)

celery_app.autodiscover_tasks(["backend.tasks"])

print("🔧 Broker:", celery_app.conf.broker_url)
print("🔧 Backend:", celery_app.conf.result_backend)

# To run the worker, use:
# celery -A backend.celery_worker worker --loglevel=info

# For windows debugging, use --pool=solo
# celery -A backend.celery_worker worker --loglevel=info --pool=solo