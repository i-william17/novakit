from celery import Celery
from config.config import settings

celery_app = Celery(
    "fastapi_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND or None,
)

celery_app.conf.update(
    task_routes={"app.tasks.*": {"queue": "default"}},
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Nairobi",
    enable_utc=False,  # Celery will use given timezone
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
    task_annotations={"*": {"max_retries": 3, "time_limit": 300}},
    result_expires=3600,
)
