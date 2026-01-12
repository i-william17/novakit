import logging
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from config.config import settings

logger = logging.getLogger("app.rate")


# ------------------------------------------------------------------------------
#  SIMPLE FALLBACK RATE LIMITER
# ------------------------------------------------------------------------------
class SimpleRateLimiter:
    def __init__(self, calls: int, window: int):
        self.calls = calls
        self.window = window  # seconds
        self.storage = defaultdict(lambda: deque())

    def allow(self, key: str) -> bool:
        q = self.storage[key]
        now = time.time()

        # Remove expired timestamps
        while q and q[0] <= now - self.window:
            q.popleft()

        # Allow request?
        if len(q) < self.calls:
            q.append(now)
            return True

        return False


# dynamic rate defined in settings
simple_limiter = SimpleRateLimiter(
    calls=getattr(settings, "RATE_LIMIT_PER_MINUTE", 60),
    window=60
)


# ------------------------------------------------------------------------------
#  UNIVERSAL RATE LIMIT MIDDLEWARE
# ------------------------------------------------------------------------------
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Universal Rate Limiter:
        Priority:
            1. fastapi-limiter (Redis)
            2. SlowAPI
            3. Simple in-memory fallback
    """

    async def dispatch(self, request: Request, call_next):

        backend = getattr(settings, "RATE_LIMIT_BACKEND", "fastapi-limiter")

        # -------------------------
        # 1️⃣ FastAPI-Limiter
        # -------------------------
        if backend == "fastapi-limiter":
            try:
                from fastapi_limiter import FastAPILimiter
                if getattr(FastAPILimiter, "_redis", None):
                    # Redis initialized → rely on decorators
                    return await call_next(request)
            except Exception:
                pass  # Redis not ready → fallback

        # -------------------------
        # 2️⃣ SlowAPI
        # -------------------------
        if backend == "slowapi":
            try:
                from slowapi.errors import RateLimitExceeded
                # slowapi normally works via route decorators; middleware is NOOP
                return await call_next(request)
            except Exception:
                pass  # fallback

        # -------------------------
        # 3️⃣ Simple global limiter
        # -------------------------
        ip = request.client.host if request.client else "unknown"

        if not simple_limiter.allow(ip):
            logger.warning("Rate limit exceeded for IP %s", ip)
            return JSONResponse(
                {"detail": "Too Many Requests"},
                status_code=429
            )

        return await call_next(request)
