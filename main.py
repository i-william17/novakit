from scalar_fastapi import (
    get_scalar_api_reference,
    Layout,
)
import logging
import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.kernel import boot
from app.common.db.sessions import close_db
from app.core.security.auth_middleware import AuthMiddleware
from config.config import settings
from app.core.router_registry import register_routes
from prometheus_fastapi_instrumentator import Instrumentator

logger = logging.getLogger("novakit.main")


def custom_generate_unique_id(route: APIRoute) -> str:
    """unique id generator used in the template."""
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
        register_routes(app)
        logger.info("Routes registered.")
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

    # Disable default docs
    # docs_url=None,
    # redoc_url=None,

    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)


Instrumentator().instrument(app).expose(app)

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

app.add_middleware(
    AuthMiddleware,
    safe_endpoints=settings.safe_endpoints,
    secret_key=getattr(settings, "SECRET_KEY", None),
    algorithm=getattr(settings, "JWT_ALGORITHM", "HS256"),
    allow_cookie_refresh=True,  # Accept refresh_token from cookies if needed
)
logger.info("Auth middleware installed.")


# 4) Register remaining middlewares via registry (this enforces order)
# try:
#     register_middlewares(app)
# except Exception as exc:
#     import logging
#     .getLogger("novakit.main").critical("Middleware registration failed: %s", exc)
#     raise


# If you have a central register_routes function,
# call it here to register controllers that use your own pattern.
# try:
#     register_routes(app)  # your function should add routers to `app`
#     logger.info("Registered routes via register_routes().")
# except Exception:
#     logger.debug("register_routes() not found or raised — continuing.")


# ------------------------------
# OpenAPI (Swagger) – Bearer JWT
# ------------------------------
# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
#
#     openapi_schema = get_openapi(
#         title=settings.APP_NAME,
#         version=settings.APP_VERSION,
#         description=settings.APP_DESCRIPTION,
#         routes=app.routes,
#     )
#
#     openapi_schema.setdefault("components", {})
#     openapi_schema["components"]["securitySchemes"] = {
#         "BearerAuth": {
#             "type": "http",
#             "scheme": "bearer",
#             "bearerFormat": "JWT",
#         }
#     }
#
#     # Apply globally (Swagger will send Authorization header automatically)
#     openapi_schema["security"] = [
#         {"BearerAuth": []}
#     ]
#
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema
#
#
# app.openapi = custom_openapi

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

@app.get("/scalar", include_in_schema=False)
async def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=f"{settings.APP_NAME} API Reference",

        layout=Layout.MODERN,
        dark_mode=True,

        persist_auth=True,  # JWT stays in browser
        hide_models=False,
        hide_search=False,
    )
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
