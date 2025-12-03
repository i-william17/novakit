import logging
import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.kernel import boot
from app.common.db.sessions import close_db
from app.api.main import api_router   
from config.config import settings  
from app.core.router_registry import register_routes  # optional existing router registry

logger = logging.getLogger("novakit.main")


def custom_generate_unique_id(route: APIRoute) -> str:
    """Keep the original unique id generator used in the template."""
    tags = route.tags or ["default"]
    return f"{tags[0]}-{route.name}"


# ------------------------------
# Lifespan context (startup/shutdown)
# ------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # run boot steps (connect to DB, create indices, register background tasks, etc.)
    try:
        logger.info("Booting application...")
        # If your boot() expects `app` pass it; adjust as needed.
        await boot(app)
        yield
    except Exception:
        logger.exception("Error during startup")
        raise
    finally:
        # shutdown tasks
        try:
            await close_db()
            logger.info("DB closed.")
        except Exception:
            logger.exception("Error while closing DB")


# ------------------------------
# App instance
# ------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=getattr(settings, "APP_VERSION", None),
    description=getattr(settings, "APP_DESCRIPTION", None),
    openapi_url=f"{getattr(settings, 'API_V1_STR', '/api/v1')}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# ------------------------------
# Sentry (optional)
# ------------------------------
if getattr(settings, "SENTRY_DSN", None) and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)
    logger.info("Sentry initialized.")


# ------------------------------
# CORS
# ------------------------------
# prefer all_cors_origins (computed property) but fall back to all_cors if needed
cors_origins = None
if hasattr(settings, "all_cors_origins"):
    cors_origins = settings.all_cors_origins
elif hasattr(settings, "all_cors"):
    cors_origins = settings.all_cors

if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware installed.")


# ------------------------------
# Include routers (API + module routes)
# ------------------------------
# Keep your existing api_router (if you still use it)
if "api_router" in globals() and api_router:
    app.include_router(api_router, prefix=getattr(settings, "API_V1_STR", "/api/v1"))
    logger.info("Included api_router at %s", getattr(settings, "API_V1_STR", "/api/v1"))

# If you have a central register_routes function (your MVC router registry),
# call it here to register controllers that use your own pattern.
try:
    register_routes(app)  # your function should add routers to `app`
    logger.info("Registered routes via register_routes().")
except Exception:
    logger.debug("register_routes() not found or raised — continuing.")


# ------------------------------
# Root health/info endpoint
# ------------------------------
@app.get("/", tags=["root"])
async def read_root():
    return {
        "id": getattr(settings, "APP_ID", getattr(settings, "APP_NAME", "novakit")),
        "description": getattr(settings, "APP_DESCRIPTION", None),
        "name": getattr(settings, "APP_NAME", None),
        "environment": getattr(settings, "ENVIRONMENT", None),
        "version": getattr(settings, "APP_VERSION", None),
        "database": {
            "host": getattr(settings, "DB_HOST", None),
            "name": getattr(settings, "DB_NAME", None),
            "driver": getattr(settings, "DB_DRIVER", None),
        },
    }


# ------------------------------
# Uvicorn runner (when executed directly)
# ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=getattr(settings, "HOST", "0.0.0.0"),
        port=int(getattr(settings, "PORT", 8099)),
        reload=bool(getattr(settings, "DEBUG", False)),
        log_level="info",
    )
