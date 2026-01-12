from fastapi import status
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
from pydantic import BaseModel
import time, psutil, logging

from app.common.base_controller import BaseController, route
from app.core.router import create_module_router

from app.core.utils.health_utils import run_health_checks
from app.core.cache.cache_utils import get_cache, set_cache
from app.common.tasks.email_tasks import send_email_task
from app.core.mailer import mail
from app.ws.redis_pubsub import redis_pubsub
from config.config import settings


class DefaultController(BaseController):
    def __init__(self):
        self.router = create_module_router("main", tags=["Main"])
        self.logger = logging.getLogger("main.endpoint")
        self.start_time = time.time()

        # automatic collection of @route methods
        self.register_routes()

    # ------------------------
    # HEALTH CHECK ENDPOINT
    # ------------------------
    @route("get", "/health", summary="System health and uptime check")
    async def health_check(self):
        uptime = round(time.time() - self.start_time, 2)
        checks = await run_health_checks()

        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
                "used_gb": round(psutil.virtual_memory().used / (1024 ** 3), 2),
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total_gb": round(psutil.disk_usage('/').total / (1024 ** 3), 2),
                "used_gb": round(psutil.disk_usage('/').used / (1024 ** 3), 2),
                "percent": psutil.disk_usage('/').percent,
            },
            "boot_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(psutil.boot_time())),
        }

        overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
        http_status = status.HTTP_200_OK if overall == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            content={
                "status": overall,
                "uptime_seconds": uptime,
                "environment": settings.ENVIRONMENT,
                "checks": checks,
                "system_metrics": system_metrics,
            },
            status_code=http_status,
        )

    # ------------------------
    # DEBUG
    # ------------------------
    @route("get", "/debug/log", summary="Emit sample log entries")
    async def test_logging(self):
        self.logger.info("Info: normal operation")
        self.logger.warning("Warning: possible issue")
        self.logger.error("Error: something went wrong")
        return {"message": "Logs emitted"}

    @route("post", "/debug/broadcast", summary="Send debug broadcast via Redis Pub/Sub")
    async def debug_broadcast(self, message: str, channel: str = None):
        payload = {"event": "debug_broadcast", "payload": {"message": message}, "channel": channel}
        await redis_pubsub.publish(payload)
        return {"ok": True}

    # ------------------------
    # CACHE
    # ------------------------
    @route("get", "/cache/decorated", summary="Demo: cached response (30s)")
    @cache(expire=30)
    async def get_cached_items(self):
        return {"message": "fresh data", "value": 123}

    @route("get", "/cache/manual-set", summary="Manually set cache key")
    async def manual_set(self, key: str, value: str):
        await set_cache(key, value, expire=120)
        return {"status": "ok", "key": key, "value": value}

    @route("get", "/cache/manual-get", summary="Manually get cache key")
    async def manual_get(self, key: str):
        return {"key": key, "value": await get_cache(key)}

    # ------------------------
    # QUEUE
    # ------------------------
    @route("post", "/queue/enqueue-bulk", summary="Queue bulk email tasks")
    async def enqueue_bulk_emails(self):
        for i in range(1, 101):
            send_email_task.delay(to=f"user{i}@example.com", name=f"User {i}")
        return {"status": "queued", "count": 100}

    # ------------------------
    # MAIL
    # ------------------------
    class MailRequest(BaseModel):
        email: str
        name: str

    @route("post", "/mail/send-test", summary="Send test email via template")
    async def send_test_email(self, payload: MailRequest):
        result = await mail.send_mail(
            to=payload.email,
            subject="FastAPI Test Email",
            template_name="test_mail.html",
            context={"name": payload.name},
        )
        return {"status": "sent" if result else "failed", "to": payload.email}


# THIS is what autoloader expects:
controller = DefaultController()
router = controller.router
