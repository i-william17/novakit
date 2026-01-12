from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp
from app.core.security.ip_blocker import IPBlocker

class IPBlockMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request, call_next):
        ip = request.client.host if request.client else "unknown"
        if await IPBlocker.is_blocked(ip):
            return JSONResponse({"detail": "Too many requests from your IP (temporarily blocked)"}, status_code=429)
        return await call_next(request)
