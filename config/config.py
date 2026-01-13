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

#
# class SystemConfig:
#     _instance = None
#     _settings_cache: dict[str, Any] = {}
#
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(SystemConfig, cls).__new__(cls)
#         return cls._instance
#
#     async def load_settings(self, db: AsyncSession):
#         # Import inside method to avoid Circular Import errors
#         from app.modules.main.repositories.settings_repository import SettingsRepository
#
#         repo = SettingsRepository(db)
#
#
#         all_settings = await repo.list_active()
#
#
#         self._settings_cache = {}
#         for s in all_settings:
#
#             val = s.current_value if s.current_value is not None else s.default_value
#             self._settings_cache[s.key] = val
#
#
#         print(f"Loaded {len(self._settings_cache)} dynamic settings into memory.")
#
#     def get(self, key: str, default: Any = None) -> Any:
#         if key in self._settings_cache:
#             return self._settings_cache[key]
#         env_value = getattr(settings, key.upper(), None)
#         if env_value is not None:
#             return env_value
#         return default
#
#     def set_manual(self, key: str, value: Any):
#         self._settings_cache[key] = value
#
#
#
# config = SystemConfig()
