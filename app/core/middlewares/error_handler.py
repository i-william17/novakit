import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.errors")

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.exception("Unhandled exception")
            return JSONResponse(
                {"detail": "Internal Server Error"},
                status_code=500,
            )
