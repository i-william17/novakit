import secrets
import warnings
from typing import Any, Annotated, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    PostgresDsn,
    # HttpUrl,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings


# -----------------------------
#  CORS Parsing
# -----------------------------
def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)


# ================================================================
#  UNIFIED COMMON CONFIG
# ================================================================
class CommonConfig(BaseSettings):
    class Config:
        env_file = ".env"
        case_sensitive = False

    # ============================================================
    #  GENERAL APPLICATION
    # ============================================================
    APP_NAME: str
    APP_VERSION: str
    APP_DESCRIPTION: str
    APP_ID: str
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    DEBUG: bool = True
    TIMEZONE: str = "Africa/Nairobi"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DOMAIN: str = "localhost"
    
    SENTRY_DSN: str | None = None

    # ============================================================
    #  FRONTEND / CORS
    # ============================================================
    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []
    
    API_V1_STR: str = "/api/v1"

    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5173"

    # Safe endpoints (comma-separated string)
    SAFE_ENDPOINTS: str = "/,/docs,/openapi.json"

    @property
    def safe_endpoints(self) -> set[str]:
        if not self.SAFE_ENDPOINTS:
            return set()

        return {
            ep.strip().rstrip("/")
            for ep in self.SAFE_ENDPOINTS.split(",")
            if ep.strip()
        }

    @computed_field
    @property
    def all_cors(self) -> list[str]:
        # combine manually set CORS + frontend host
        return [str(o).rstrip("/") for o in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]
        
    @property
    def all_cors_origins(self) -> list[str]:
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [i.strip() for i in self.BACKEND_CORS_ORIGINS.split(",") if i.strip()]
        return self.BACKEND_CORS_ORIGINS

    # ============================================================
    #  SECURITY / JWT
    # ============================================================
    SECRET_KEY: str = secrets.token_urlsafe(32)

    JWT_SECRET_KEY: str = "836abbf2d3ddf8555e88cc3b84ddb863205f26f51d2edccee5918b6902507362"
    JWT_ALGORITHM: str = "HS256"

    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    BRUTE_FORCE_ATTEMPTS: int = 5
    BRUTE_FORCE_WINDOW: int = 300
    BRUTE_FORCE_LOCKOUT: int = 600

    # Brute / IP blocking
    IP_DISTINCT_USERNAME_THRESHOLD: int = 10
    IP_DISTINCT_WINDOW: int = 300  # seconds
    IP_BLOCK_LOCKOUT: int = 3600  # seconds

    # toggles
    ENABLE_IP_BLOCKING: bool = True
    ENABLE_BRUTE_FORCE_PROTECTION : bool = True

    # Superuser
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # ============================================================
    #  POSTGRES DATABASE
    # ============================================================
    DB_DRIVER: str
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    SYNC_DATABASE_URL: str
    
    DB_ECHO: bool = False

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme=self.DB_DRIVER.replace("+asyncpg", "+psycopg"),
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=f"/{self.DB_NAME}",
        )

    # ============================================================
    #  RABBITMQ
    # ============================================================
    BROKER_HOST: str
    BROKER_PORT: int = 5672
    BROKER_VHOST: str = "dev"
    BROKER_USERNAME: str
    BROKER_PASSWORD: str

    BROKER_URL: str

    # ============================================================
    #  REDIS CACHE
    # ============================================================
    CACHE_HOST: str
    CACHE_PORT: int = 6379
    CACHE_PASSWORD: str
    CACHE_DB: int = 0

    REDIS_URL: str
    
    ENABLE_REDIS_CACHE: bool = True
    CACHE_BACKEND: str = "redis"   # "redis" or "memory"
    REDIS_URL: str = "redis://localhost:6379/0"
    FASTAPI_CACHE_PREFIX: str = "fastapi-cache"

    # ============================================================
    #  MONGO LOG DATABASE
    # ============================================================
    LOG_DB_HOST: str
    LOG_DB_PORT: int
    LOG_DB_NAME: str
    LOG_DB_USER: str
    LOG_DB_PASSWORD: str

    MONGO_URL: str

    # ============================================================
    #  LOGGING CONFIG
    # ============================================================
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_FILE_LEVELS: str = "info,warning,error"

    LOG_TO_MONGO: bool = True
    LOG_MONGO_LEVELS: str = "error,warning"
    MONGO_LOG_COLLECTION: str = "app-logs"

    # ============================================================
    #  CELERY
    # ============================================================
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # ============================================================
    #  SMTP MAIL CONFIG
    # ============================================================
    MAIL_HOST: str | None = None
    MAIL_PORT: int = 587
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None

    MAIL_USE_TLS: bool = True
    MAIL_USE_SSL: bool = False

    SYSTEM_ADMIN_EMAIL: EmailStr | None = None
    MAIL_FROM_NAME: str | None = None

    @computed_field
    @property
    def emails_enabled(self) -> bool:
        return bool(self.MAIL_HOST and self.MAIL_USERNAME)

    @model_validator(mode="after")
    def _default_mail_name(self):
        if not self.MAIL_FROM_NAME:
            self.MAIL_FROM_NAME = self.APP_NAME
        return self

    # ============================================================
    #  SECURITY VALIDATION (PRODUCTION SAFE)
    # ============================================================
    def _check_default(self, name: str, value: str | None):
        if value in ["changeme", "change_me_please", "changethis"]:
            msg = f"⚠ SECURITY WARNING: '{name}' uses a weak default value!"
            if self.ENVIRONMENT == "local":
                warnings.warn(msg)
            else:
                raise ValueError(msg)

    @model_validator(mode="after")
    def _validate_security(self):
        self._check_default("SECRET_KEY", self.SECRET_KEY)
        self._check_default("DB_PASSWORD", self.DB_PASSWORD)
        self._check_default("FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD)
        return self

 
