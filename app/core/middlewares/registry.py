from typing import List, Tuple
from fastapi import FastAPI
from config.config import settings

# map keys -> (import path, class_name)
AVAILABLE = {
    "cors": None,  # handled by FastAPI.add_middleware(CORSMiddleware) earlier
    "request_id": "app.middlewares.request_id.RequestIDMiddleware",
    "request_logger": "app.middlewares.request_logger.RequestLoggingMiddleware",
    "process_time": "app.middlewares.process_time.ProcessTimeMiddleware",
    "session_cookie": "app.middlewares.session_cookie.CookieSessionMiddleware",
    "auth": "app.core.security.auth_middleware.AuthMiddleware",  # your auth middleware path
    "rate_limit": "app.middlewares.rate_limiter.RateLimitMiddleware",
    "security_headers": "app.middlewares.security_headers.SecurityHeadersMiddleware",
    "trailing_slash": "app.middlewares.trailing_slash.TrailingSlashMiddleware",
    "error_handler": "app.middlewares.error_handler.ErrorHandlerMiddleware",
    "maintenance": "app.middlewares.maintenance_mode.MaintenanceModeMiddleware",
    # gzip is added via FastAPI middleware GZipMiddleware (no import string here)
}

# required ordering: CORS must be before auth; auth before request handlers.
REQUIRED_ORDER = [
    "cors",            # MUST be first (handled separately)
    "request_id",      # correlation id early
    "process_time",
    "request_logger",
    "session_cookie",
    "auth",            # auth should be before rate limiting or after? choose before rate limiting to allow user-based limits
    "rate_limit",
    "security_headers",
    "trailing_slash",
    "maintenance",
    "error_handler",
]


def _import_class(path: str):
    module_name, class_name = path.rsplit(".", 1)
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)


def validate_order(enabled: List[str]):
    """
    Ensure that enabled middlewares preserve relative order defined in REQUIRED_ORDER.
    """
    # keep only those that are in REQUIRED_ORDER and enabled
    filtered = [m for m in REQUIRED_ORDER if m in enabled]
    enabled_filtered = [m for m in enabled if m in REQUIRED_ORDER]
    # enabled_filtered must equal filtered (relative order preserved)
    if enabled_filtered != filtered[: len(enabled_filtered)]:
        raise RuntimeError(
            f"Middleware order invalid. Expected order (subset) {filtered} ; got {enabled_filtered}. "
            "This is a security-sensitive configuration; aborting startup."
        )


def register_middlewares(app: FastAPI):
    """
    Read settings.MIDDLEWARES (list of keys) to decide what to register and in what order.
    Raises on missing/invalid order.
    """
    # settings.MIDDLEWARES should be a list of strings like ["request_id", "process_time", "auth", ...]
    enabled = getattr(settings, "MIDDLEWARES", [])
    if not isinstance(enabled, list):
        raise RuntimeError("settings.MIDDLEWARES must be a list")

    # Validate order
    try:
        validate_order(enabled)
    except Exception as e:
        raise

    # Register each middleware
    for key in enabled:
        if key == "cors":
            # CORS should already been applied early in main.py
            continue
        path = AVAILABLE.get(key)
        if path is None:
            # unknown or handled elsewhere (gzip etc)
            continue
        cls = _import_class(path)
        # If auth middleware needs kwargs, pass settings via add_middleware below in main
        app.add_middleware(cls)
