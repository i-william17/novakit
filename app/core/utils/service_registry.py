from fastapi import FastAPI
import logging
from typing import Any

logger = logging.getLogger(__name__)


def log_registered_services(app: FastAPI) -> None:
    """
    Logs all services registered in app.state in a clean, readable format.

    Similar to Yii::$app service locator dump.
    """
    state = getattr(app.state, "_state", None)

    if not state:
        logger.info("No application services registered.")
        return

    logger.info("Application services registered:")

    for name, service in state.items():
        logger.info(
            "  • %-20s -> %s",
            name,
            _describe_service(service),
        )


def _describe_service(service: Any) -> str:
    """
    Returns a readable description of a service instance.
    """
    try:
        cls = service.__class__.__name__

        # Special handling for SQLAlchemy async sessionmaker
        if cls == "async_sessionmaker":
            return "AsyncSessionMaker"

        return cls
    except Exception:
        return str(service)
