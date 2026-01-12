from dataclasses import dataclass
from config.config import settings

@dataclass
class AppContext:
    env: str
    settings: object

def get_context() -> AppContext:
    return AppContext(
        env=settings.ENV,
        settings=settings,
    )
