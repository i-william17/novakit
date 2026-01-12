from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class CookieSessionMiddleware(BaseHTTPMiddleware):
    """
    Minimal cookie parser that sets request.state.cookies for convenience.
    Not a full session store — plug your session backend if needed.
    """
    async def dispatch(self, request: Request, call_next):
        request.state.cookies = request.cookies
        return await call_next(request)
