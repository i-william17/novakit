    Access services:

    API Gateway: http://localhost

    Auth Service: http://localhost:8001

    Accounting Service: http://localhost:8002

    NOC Service: http://localhost:8003

    RabbitMQ Management: http://localhost:15672 (admin/securepassword123)

    Grafana: http://localhost:3000 (admin/admin123)

    Prometheus: http://localhost:9090










auth-service/
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── ... (auth-specific migrations)
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   └── roles.py
│   │   └── health.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── role.py
│   │   └── permission.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   └── role.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   └── token_service.py
│   ├── events/
│   │   ├── __init__.py
│   │   ├── handlers.py
│   │   └── schemas.py
│   └── db/
│       ├── __init__.py
│       └── session.py  # Uses shared database














# auth-service/app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from shared.database.connection import init_db, close_db
from shared.messaging.rabbitmq import get_event_bus, AsyncEventBus
from shared.auth.middleware import MicroserviceAuthMiddleware
from app.api import v1
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Auth Service...")
    
    # Initialize database with auth schema
    await init_db(
        app=app,
        schema="auth",
        echo=settings.DB_ECHO
    )
    
    # Initialize event bus
    event_bus = await get_event_bus()
    
    # Register event handlers
    from app.events import handlers
    await handlers.register_handlers(event_bus)
    
    # Publish service started event
    await event_bus.publish_event(
        "service_started",
        {
            "service": "auth",
            "status": "running",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down Auth Service...")
    await event_bus.publish_event(
        "service_stopped",
        {
            "service": "auth",
            "status": "stopped",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    await close_db()
    if event_bus.client:
        await event_bus.client.close()

# Create FastAPI app
app = FastAPI(
    title="Auth Service",
    description="Authentication and Authorization Microservice",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add auth middleware (auth service doesn't need to validate with itself)
app.add_middleware(
    MicroserviceAuthMiddleware,
    safe_endpoints={"/health", "/docs", "/openapi.json", "/redoc", "/auth/login", "/auth/register"},
    validate_with_auth_service=False
)

# Include routers
app.include_router(v1.auth.router, prefix="/auth/v1", tags=["authentication"])
app.include_router(v1.users.router, prefix="/auth/v1", tags=["users"])
app.include_router(v1.roles.router, prefix="/auth/v1", tags=["roles"])

# Health endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "auth",
        "timestamp": datetime.utcnow().isoformat()
    }

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    # Return Prometheus metrics
    return {"metrics": "to_be_implemented"}