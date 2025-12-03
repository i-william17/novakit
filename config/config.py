from pydantic_settings import SettingsConfigDict
from .common import CommonConfig
from .web import WebConfig
from .console import ConsoleConfig


class Settings(CommonConfig, WebConfig, ConsoleConfig):
    """
    Unified application configuration.
    Combines: Common + Web + Console
    """

    model_config = SettingsConfigDict(
         env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",          # ignore unknown env vars
        case_sensitive=False
    )
    


# final global settings instance
settings = Settings()
