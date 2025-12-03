from app.core.celery_app import celery
import redis, json
from app.core.config import settings

@celery.task
def send_notification(payload: dict):
    # using redis sync client for simplicity in Celery
    r = redis.Redis.from_url(settings.REDIS_URL)
    r.publish("ws-broadcast", json.dumps(payload))
