import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("app.request")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        rid = getattr(request.state, "request_id", "-")
        user = getattr(request.state, "user", {}).get("sub") if hasattr(request.state, "user") else None

        logger.info(
            "%s %s %s %s %d %.2fms",
            request.client.host if request.client else "-",
            request.method,
            request.url.path,
            f"user={user}" if user else "",
            response.status_code,
            duration_ms,
        )
        return response
