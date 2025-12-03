from typing import Any, Annotated
from pydantic import BeforeValidator
from pydantic_settings import BaseSettings


def parse_cors(v: Any) -> list[str] | str:
    """
    Allows CORS format:
    - "http://a.com,http://b.com"
    - ["http://a.com", "http://b.com"]
    - "*"
    """
    if isinstance(v, str):
        if v.strip() == "*":
            return ["*"]
        if "," in v:
            return [i.strip() for i in v.split(",") if i.strip()]
    if isinstance(v, list):
        return v
    return v


class WebConfig(BaseSettings):
    """
    Web-only configuration.
    Anything shared with CommonConfig should NOT be here.
    """

    # ===================================================
    # WEB SERVER SPECIFIC
    # ===================================================
    # HOST: str = "0.0.0.0"
    # PORT: int = 8000

    # ===================================================
    # FRONTEND / DOMAIN
    # ===================================================
    # DOMAIN: str = "localhost"
    # FRONTEND_HOST: str = "http://localhost:5173"

    # ===================================================
    # CORS
    # ===================================================
    # BACKEND_CORS_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors)] = ["*"]
    ALLOWED_HOSTS: str = "*"

    # ===================================================
    # RATE LIMITING
    # ===================================================
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60

    # ===================================================
    # FEATURE FLAGS
    # ===================================================
    ENABLE_AUDIT_LOGS: bool = True
    ENABLE_WEBSOCKETS: bool = True
    ENABLE_CELERY: bool = True
    ENABLE_REDIS_CACHE: bool = True

    # ===================================================
    # COOKIES
    # ===================================================
    SESSION_COOKIE_NAME: str = "sessionid"
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"

    # ===================================================
    # MAIL (ONLY PRESENTATION, NOT CREDENTIALS)
    # Keep only what is needed for API email sending display
    # Actual credentials exist already in CommonConfig
    # ===================================================
    MAIL_FROM_NAME: str = "NovaKit"

