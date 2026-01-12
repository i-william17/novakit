from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """
    Normalize trailing slashes by redirecting paths with trailing slash
    to without one (unless path == "/").
    """
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path != "/" and path.endswith("/"):
            new = path.rstrip("/") or "/"
            # preserve query
            qs = request.url.query
            if qs:
                new = f"{new}?{qs}"
            return RedirectResponse(url=new)
        return await call_next(request)
