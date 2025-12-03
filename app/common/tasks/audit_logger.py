from app.core.celery_app import celery
from datetime import datetime
from pymongo import MongoClient
from app.core.config import settings

mongo = MongoClient(settings.MONGO_URL)[settings.LOG_DB_NAME]

@celery.task(bind=True)
def log_task(self, task_name, status, metadata=None):
    mongo.task_logs.insert_one({
        "task": task_name,
        "status": status,
        "metadata": metadata or {},
        "timestamp": datetime.utcnow(),
    })
