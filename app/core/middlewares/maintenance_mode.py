from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from config.config import settings

class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if getattr(settings, "MAINTENANCE_MODE", False):
            return JSONResponse({"detail": "Service under maintenance"}, status_code=503)
        return await call_next(request)
