# NovaKit Boilerplate — Setup & Developer Guide

This document explains **how to set up, run, and extend the NovaKit boilerplate**. It is written for team members who are new to the project and should be followed **step by step**.

---

## ⚠️ Important Notice

This boilerplate was developed rapidly and is still evolving.

Some steps may fail depending on your environment

Some APIs and folders may change in future updates

If you hit an error, share it and we’ll fix it.
Future updates will extend the structure — not break it.

## 1. Prerequisites

Make sure you have the following installed:

* Docker ≥ 20.x
* Docker Compose ≥ v2
* Git

Optional (Bare-Metal / Local Dev)
* Python 3.10+
* Poetry

NovaKit is designed to run **fully containerized**. You do not need Python installed locally unless you want to run tools outside Docker.

---

## 2. Project Structure (High Level)

```
project-root/
├── app/                    # Application source code
│   ├── core/               # Kernel, middleware, router registry
│   ├── common/             # Shared utilities (db, helpers)
│   ├── modules/            # Feature modules (iam, bookings, etc)
│--config/               # Environment-based configuration
│   │   ├── __init__.py
│   │   ├── common.py         # Shared settings
│   │   ├── web.py            # API / HTTP app settings
│   │   ├── console.py        # CLI (future)
│   │   └── config.py         # Settings loader   
│
├── docker/                 # Docker-related configs (optional)
├── scripts/                # Helper scripts (boot, cli, etc)
├── docs/                   # Extra documentation (alembic.md, etc)
├── docker-compose.yml      # Containers (DB, Redis, RabbitMQ, etc)
├── Dockerfile              # App container
├── pyproject.toml
├── uv.lock
└── SETUP.md                # This file
└── main.py             # FastAPI entry point
└── .env             # FastAPI entry point
```

---

## Configuration System (IMPORTANT)

### NovaKit uses a layered config system.

config/
```
| File         | Purpose                               |
| ------------ | ------------------------------------- |
| `common.py`  | Shared settings (used everywhere)     |
| `web.py`     | HTTP / API app settings               |
| `console.py` | CLI settings (future)                 |
| `config.py`  | Loads env vars and exposes `settings` |
```

## Environment Variables (.env)
Create a .env file in the project root.
### Recommended Base .env

```
############################################
# GENERAL APPLICATION SETTINGS
############################################
APP_NAME="Novakit"
APP_VERSION="1.0.0"
APP_DESCRIPTION="Novakit boilerplate."
APP_ID="novakit-api"
TIMEZONE="Africa/Nairobi"
ENVIRONMENT="local"
DEBUG=true

HOST="0.0.0.0"
PORT=8099

############################################
# DOMAIN & FRONTEND
############################################
DOMAIN="localhost"
FRONTEND_HOST="http://localhost:5173"

############################################
# CORS
############################################
BACKEND_CORS_ORIGINS="http://localhost,http://localhost:5173"

############################################
# SECURITY (JWT)
############################################
JWT_SECRET_KEY="836abbf2d3ddf8555e88cc3b84ddb863205f26f51d2edccee5918b6902507362"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

SECRET_KEY="d689f0d1ccda700f75ce0c201af71a385c704799baacd4d5d067a0c46add8e29"

############################################
# BRUTE FORCE / SECURITY
############################################
BRUTE_FORCE_ATTEMPTS=5
BRUTE_FORCE_WINDOW=300
BRUTE_FORCE_LOCKOUT=600

IP_DISTINCT_USERNAME_THRESHOLD=10
IP_DISTINCT_WINDOW=300
IP_BLOCK_LOCKOUT=3600

ENABLE_IP_BLOCKING=true
ENABLE_BRUTE_FORCE_PROTECTION=true

############################################
# DATABASE (PostgreSQL)
############################################
DB_DRIVER=postgresql
DB_HOST=postgresql
DB_PORT=5432
DB_NAME=novakit
DB_USER=root
DB_PASSWORD=root

############################################
# REDIS
############################################
REDIS_HOST=redisv1
REDIS_PORT=6379
REDIS_PASSWORD=root
```

## 3. Containers & Services

NovaKit uses multiple infrastructure services via Docker Compose.

### Included Services

| Service       | Purpose                   | Port            |
| ------------- | ------------------------- | --------------- |
| MariaDB       | Optional relational DB    | 3306 (internal) |
| PostgreSQL    | Primary relational DB     | 5452 → 5432     |
| MSSQL         | Optional enterprise DB    | 1433            |
| MongoDB       | Document DB               | 28017 → 27017   |
| Redis         | Cache / sessions / queues | 6369 → 6379     |
| RabbitMQ      | Messaging / async jobs    | 5666 / 88       |
| Prometheus    | Metrics                   | 9500            |
| Grafana       | Dashboards                | 9022            |
| pgAdmin       | Postgres UI               | 84              |
| phpMyAdmin    | MariaDB UI                | 81              |
| Mongo Express | MongoDB UI                | 83              |

> ⚠️ **Important**
>
> * You may change **ports, IPs, volumes, and network names** freely.
> * The provided IP addresses assume a shared Docker network named `shared`.

---

## 4. Docker Network

Create the shared network **once**:

```bash
docker network create \
  --subnet=172.20.0.0/16 \
  shared
```

If you already have a network, update `docker-compose.yml` accordingly.

---

## 5. Starting the Infrastructure
Start databases, cache, queues, monitoring:

From the project root/infra/docker:

```bash
docker compose up -d
```
 
This will start:

* Databases
* Redis
* RabbitMQ
* Monitoring stack

Verify containers:

```bash
docker compose ps
```

---

## 6. Application Container

### Dockerfile Summary

The app container:

* Uses **Python 3.10**
* Uses **uv** for dependency management
* Runs FastAPI with multiple workers

### Build the App Image

```bash
docker build -t novakit-app .
```

### Run the App Container

```bash
docker run --rm \
  --network shared \
  -p 8099:8099 \
  --env-file .env \
  novakit-app
```

The API will be available at:

```
http://localhost:8099
```
## OR YOU CAN RUN THE APP docker-compose.yaml (RECOMMENDED)
From the project root:

```
docker compose up --build
```

---

## 7. Environment Variables

Create a `.env` file in the project root.

### Minimal Required Variables

```env
APP_NAME=NovaKit
APP_ENV=local
APP_DEBUG=true

DB_DRIVER=postgresql
DB_HOST=postgresql
DB_PORT=5432
DB_NAME=novakit
DB_USER=root
DB_PASSWORD=root

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256

REDIS_HOST=redisv1
REDIS_PORT=6379
REDIS_PASSWORD=root
```

> 🔐 Never commit real secrets.

---


## 8. Authentication Flow (IMPORTANT)

NovaKit uses **JWT-based authentication** with a **global middleware**.

### AuthMiddleware Responsibilities

* Runs on **every request**
* Validates JWT signature & expiry
* Blocks unauthenticated access
* Does **NOT** access the database

```text
Request
  ↓
AuthMiddleware (JWT validation)
  ↓
Controller Dependency (require_login)
  ↓
Service / Business Logic
```

### request.state Usage

The middleware injects:

```python
request.state.auth = {
  "payload": jwt_payload,
  "token": raw_token,
}
```

### Loading the Current User

Database access is done **only** inside dependencies:

```python
async def require_login(request: Request, db: AsyncSession):
    payload = request.state.auth["payload"]
    user_id = payload.get("sub")
    return await repo.get_by_id(db, user_id)
```

This keeps auth **fast, safe, and testable**.

---

## 9. Module Architecture (CRITICAL)

Every feature lives inside a **module**.

### Module Layout

```
app/modules/iam/
├── controllers/     # API endpoints (HTTP only)
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas (IO only)
├── repositories/    # Database access
├── services/        # Business logic
├── migrations/      # (Future) module-level migrations
└── __init__.py
```

---

## 10. Where Logic Belongs

| Layer      | Responsibility                 |
| ---------- | ------------------------------ |
| Controller | HTTP, validation, status codes |
| Schema     | Input/output shape only        |
| Service    | Business rules, workflows      |
| Repository | SQL / DB queries only          |
| Model      | Table definition               |

❌ Controllers must NOT talk to DB directly
❌ Repositories must NOT contain business logic

---

## 11. Creating a New Module

Example: `inventory`

```bash
mkdir -p app/modules/inventory/{controllers,models,schemas,repositories,services}
```

Register routes in your controller and ensure `register_routes()` picks them up.

---

## 12. Migrations Flow

NovaKit uses **Alembic**.

### Run Existing Migrations

```bash
alembic upgrade head
```

### Create a Migration

```bash
alembic revision -m "create_users_table"
```

> 📌 For advanced migration strategies (per-module, tenant-aware, locking),
> **see `docs/alembic.md`**.

---

## 13. Typical Development Flow

1. Start containers
2. Run migrations
3. Create module
4. Create model
5. Create repository
6. Create service
7. Create schema
8. Create controller
9. Register routes

Follow this order to avoid confusion.

---

## Controllers Pattern (BaseController)

#### All controllers:

* Extend BaseController

* Use unified responses

* Register routes internally

```python
class AuthController(BaseController):
    def __init__(self):
        self.router = create_module_router("iam", tags=["IAM"])
        self.register_routes()

    @route("post", "/login")
    async def login(self, body: LoginInput, db: AsyncSession = Depends(get_db)):
        ...
```

### Route Registration

Routes are registered centrally:

```python
def register_routes(app: FastAPI):
    app.include_router(iam_auth_router, prefix="/v1/auth", tags=["IAM"])
    app.include_router(iam_router, prefix="/v1/iam", tags=["IAM"])

```
🔜 This will become automatic in future versions


## Migrations (IMPORTANT)
#### Recommended Flow

Create migration first

Run migration

Then write models
```
alembic revision -m "create_users_table"
alembic upgrade head

```

📌 Advanced migration strategies → docs/alembic.md

## 14. Health Check

```http
GET /
```

Returns app metadata and DB config.

---

## 15. Final Notes

* NovaKit is **modular by design**
* Middleware is global & early
* Auth is split into validation vs identity
* Future features (CLI, generators, per-module migrations) are planned

---

🚀 Welcome to NovaKit.
Build clean. Scale safely.

---

## Application Container (Development)

### Dockerfile (Backend)

This Dockerfile is designed to:

* Use **uv** for fast dependency resolution
* Work both on **bare metal** and **Docker**
* Connect to externally running database containers

```dockerfile
FROM python:3.10

ENV PYTHONUNBUFFERED=1
WORKDIR /app/

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install deps (cached)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

ENV PYTHONPATH=/app

COPY ./scripts /app/scripts
COPY ./pyproject.toml ./uv.lock ./alembic.ini /app/
COPY ./app /app/app
COPY ./tests /app/tests

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## Application docker-compose.yml (Development)

> This compose file assumes **database containers are already running** on the shared Docker network.

```yaml
version: "3.9"

services:
  app:
    build: .
    container_name: novakit-app
    restart: always
    env_file:
      - .env
    environment:
      APP_ENV: development
      POSTGRES_HOST: postgresql
      POSTGRES_PORT: 5432
      POSTGRES_USER: root
      POSTGRES_PASSWORD: root
      POSTGRES_DB: novakit
      REDIS_HOST: redisv1
      REDIS_PORT: 6379
      REDIS_PASSWORD: root
      RABBITMQ_HOST: rabbitmqv1
      RABBITMQ_PORT: 5672
    ports:
      - "8000:8000"
    networks:
      - shared

networks:
  shared:
    external: true
```

---

## Boot Order (IMPORTANT)

1. Start infrastructure containers:

```bash
docker compose -f infra/docker/database/docker-compose.yaml up -d
```

2. Start the application:

```bash
docker compose up --build
```

---

## Optional Bootstrap Script

`scripts/bootstrap.sh`

```bash
#!/usr/bin/env bash
set -e

echo "Starting database containers..."
docker compose -f infra/docker/database/docker-compose.yaml up -d

sleep 5

echo "Starting application container..."
docker compose up --build
```

---

## Local Development (Bare Metal)

### Create & activate virtualenv

```bash
poetry install
poetry shell
```

### Run migrations

```bash
poetry run alembic upgrade head
```

### Start API

```bash
poetry run uvicorn main:app --reload --port 8099

```

---

## Migration Notes

* Alembic is used for schema migrations
* Each module owns its migrations
* Advanced usage is documented in `docs/alembic.md`
* Always run migrations **before** starting the app

---

## Networking Notes

* Network name `shared` can be changed
* Static IPs are optional
* Ensure no port conflicts on host machine
* All service hostnames resolve via Docker DNS

---

✅ With this setup, Novakit can run:

* Bare metal (Poetry)
* Docker-only app
* Docker infra + local app
* Full Docker stack
