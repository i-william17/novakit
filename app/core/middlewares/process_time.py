import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{time.time() - start:.6f}"
        return response
