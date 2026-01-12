import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add X-Request-ID header and request.state.request_id for logs/correlation.
    """
    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get(self.header_name) or str(uuid.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        # Ensure header present on responses
        if self.header_name not in response.headers:
            response.headers[self.header_name] = rid
        return response
