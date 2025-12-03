import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config.config import settings  
from app.core.logging.mongo_log_handler import MongoLogHandler


def parse_levels(level_str: str):
    """Convert comma-separated string like 'error,warning' to list of numeric levels."""
    if not level_str:
        return []
    level_map = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }
    levels = []
    for name in level_str.split(","):
        lvl = level_map.get(name.strip().lower())
        if lvl:
            levels.append(lvl)
    return levels


class LevelFilter(logging.Filter):
    """Filter log records to allow only specific levels."""
    def __init__(self, allowed_levels):
        super().__init__()
        self.allowed_levels = allowed_levels or []

    def filter(self, record):
        return not self.allowed_levels or record.levelno in self.allowed_levels


def setup_logging():
    """Set up logging with console, file, and MongoDB handlers."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    # Console handler (always all levels)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    ch.setLevel(level)
    root.addHandler(ch)

    # File logging
    if settings.LOG_TO_FILE:
        try:
            log_file_path = Path(settings.LOG_FILE_PATH)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

            fh = RotatingFileHandler(
                str(log_file_path), maxBytes=10 * 1024 * 1024, backupCount=5
            )
            fh.setFormatter(fmt)

            allowed_file_levels = parse_levels(settings.LOG_FILE_LEVELS)
            if allowed_file_levels:
                fh.addFilter(LevelFilter(allowed_file_levels))
                fh.setLevel(min(allowed_file_levels))
            else:
                fh.setLevel(level)

            root.addHandler(fh)
        except Exception:
            logging.getLogger("uvicorn.error").exception("Failed to initialize file logging")

    # Mongo logging
    if settings.LOG_TO_MONGO:
        try:
            mh = MongoLogHandler()
            mh.setFormatter(fmt)

            allowed_mongo_levels = parse_levels(settings.LOG_MONGO_LEVELS)
            if allowed_mongo_levels:
                mh.addFilter(LevelFilter(allowed_mongo_levels))
                mh.setLevel(min(allowed_mongo_levels))
            else:
                mh.setLevel(level)

            root.addHandler(mh)
        except Exception:
            logging.getLogger("uvicorn.error").exception("Failed to initialize MongoLogHandler")

    # Optional Sentry integration
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT)
            logging.getLogger("sentry").info("Sentry initialized")
        except Exception:
            logging.getLogger("uvicorn.error").exception("Sentry init failed")
