# Novakit — FastAPI Boilerplate (README)

Welcome to **Novakit**, a FastAPI boilerplate derived from the Full‑Stack FastAPI Template. This README documents how to run the project locally **without Docker**, explains the role of Poetry and `pyproject.toml` versus `requirements.txt`, and provides step‑by‑step instructions for contributors and users.

---

## Table of contents

1. About
2. Why Poetry?
3. `pyproject.toml` vs `requirements.txt` — which to use
4. Prerequisites
5. Project structure
6. Quick start (Poetry)
7. Alternative: venv + pip
8. Environment variables (`.env`) — sample
9. Database migrations (Alembic / Prisma / create_all)
10. Running the app (backend + frontend)
11. Common troubleshooting
12. Developer notes & tips
13. Contributing
14. License

---

## 1. About

Novakit is a structured boilerplate for building production‑ready FastAPI apps. It includes common features such as configuration via `.env`, DB setup, prestart scripts, and a Vite frontend. This README helps you run the stack locally without Docker and explains the tooling choices.

---

## 2. Why Poetry?

**Poetry** is a modern Python dependency manager and packaging tool that provides:

* Declarative dependency specification (`pyproject.toml`).
* Deterministic installs via `poetry.lock`.
* Virtual environment management (isolated per project).
* Build and publish workflows integrated.

Benefits vs older workflows:

* Single source (`pyproject.toml`) covers metadata, dependencies, and build-backend.
* Built-in handling of dev vs prod dependencies.
* Cleaner reproducible installs compared to ad-hoc `pip install` sequences.

Poetry is the recommended tool for Novakit, but an alternative pip/venv workflow is provided below.

---

## 3. `pyproject.toml` vs `requirements.txt`

* **`pyproject.toml`** (with Poetry): describes the project, its dependencies, optional extras, and tooling configuration. Use this when you want reproducible dev environments, more metadata, and better packaging.

* **`requirements.txt`**: a flat list of packages (often with pinned versions). It is simple and portable but lacks metadata and fine-grained dependency/extras support.

**Recommendation:** Use `pyproject.toml` + Poetry for development, CI, and packaging. Provide a generated `requirements.txt` for users who must use `pip` only (Poetry can export a requirements file).

To export a requirements.txt from Poetry:

```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

---

## 4. Prerequisites

* Python 3.10+ (3.11/3.12 recommended)
* Node.js 16+ and npm/yarn/pnpm (for the frontend)
* PostgreSQL (or your chosen DB) accessible from your machine
* git (optional)

---

## 5. Project structure (typical)

```
project/
  backend/           # FastAPI app + pyproject.toml
    app/             # FastAPI package (app.main:app)
    scripts/         # prestart, create_db, helpers
    pyproject.toml
    alembic/         # migrations (if present)
  frontend/          # Vite app
  infra/             # docker + traefik compose files (optional)
  .env.example
  README.md
```

---

## 6. Quick start (Poetry — recommended)

> These steps run the backend and frontend locally without Docker.

### 1. Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
# ensure poetry is on PATH
export PATH="$HOME/.local/bin:$PATH"
poetry --version
```

### 2. Configure Poetry to put venvs inside the project (optional but helpful)

```bash
poetry config virtualenvs.in-project true
```

### 3. Install dependencies

```bash
cd backend
poetry install
```

This creates `backend/.venv/` and installs everything declared in `pyproject.toml`.

### 4. Activate the environment (two options)

**Option A — activate shell manually**

```bash
# Poetry prints the activation command; run it
poetry env info
# copy the `Path:` or `Activators` output, then run (example):
source .venv/bin/activate
```

**Option B — run commands without activating shell (recommended in CI or automation)**

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Create `.env` (sample below) and point to your DB

Place `.env` inside `backend/` (or project root if your code expects it there).

### 6. Apply migrations (if using Alembic)

```bash
poetry run alembic upgrade head
```

If using Prisma, follow the `prisma generate` / `prisma migrate` steps.

### 7. Run prestart (optional)

If the repo provides `scripts/prestart.sh`:

```bash
chmod +x scripts/prestart.sh
poetry run bash scripts/prestart.sh
```

### 8. Start backend

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs`.

### 9. Start frontend

```bash
cd ../frontend
npm install
npm run dev
```

Open the Vite URL (usually `http://localhost:5173`).

---

## 7. Alternative: venv + pip (if you don't want Poetry)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
# Option A: install via editable package if pyproject supports it
pip install -e .
# Option B: install from requirements.txt (if provided)
pip install -r requirements.txt
```

Run migrations and start uvicorn as above.

---

## 8. Environment variables (`backend/.env`) — sample

```env
# Application
PROJECT_NAME=Novakit
SECRET_KEY=change_this_to_a_strong_secret
ENVIRONMENT=development

# Database (example Postgres)
POSTGRES_USER=appuser
POSTGRES_PASSWORD=supersecret
POSTGRES_DB=appdb
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
# OR a full URL many projects support
DATABASE_URL=postgresql://appuser:supersecret@localhost:5432/appdb

# First superuser (optional)
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123
```

**Important:** Ensure the backend code reads the same env names. Update `.env` location or loader if it does not.

---

## 9. Database migrations

Novakit can support different migration strategies. Use whichever the project contains:

* **Alembic:** `poetry run alembic upgrade head` (or `alembic -c <path> upgrade head`)
* **Prisma:** `prisma generate` + `prisma migrate deploy` (run with Node/npm)
* **No migrations (SQLModel/create_all):** run `scripts/prestart.sh` or a helper script that creates tables.

If unsure, inspect `backend/` for `alembic/`, `prisma/`, or migration scripts.

---

## 10. Running the app — commands summary

Run these from `backend/` (example):

```bash
# run server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# run migrations (alembic)
poetry run alembic upgrade head

# run prestart script
poetry run bash scripts/prestart.sh
```

---

## 11. Common troubleshooting

* **`uvicorn: command not found`** — run with `poetry run ...` or activate the venv (`source .venv/bin/activate`).
* **Poetry virtualenv path errors after renaming folder** — remove stale venvs with `poetry env remove --all`, then `poetry install`.
* **DB connection refused** — check `DATABASE_URL` host/port and DB accessibility (firewall, pg_hba.conf).
* **Migrations fail** — check credentials, DB name, permissions, and migration files.
* **Frontend can't access API** — set `VITE_API_URL` to `http://localhost:8000` or `http://127.0.0.1:8000` for dev.

---

## 12. Developer notes & tips

* Lock your dependencies: `poetry lock` and check `poetry.lock` into version control.
* Export `requirements.txt` for environments that require pip: `poetry export -f requirements.txt --output requirements.txt --without-hashes`.
* Keep `virtualenvs.in-project = true` in your developer setup to avoid path breakage when renaming project folders.
* Use `poetry run` in scripts to avoid manual activation in CI.

---

## 13. Contributing

1. Fork and create a feature branch.
2. Update `pyproject.toml` and run `poetry install` locally.
3. Add tests and run them.
4. Create a PR with a clear description.

---

## 14. License

Add your license here (MIT by default if you want).

---

If you want, I can:

* Convert this README into a `README.md` file in your repo (I can create it for you),
* Create a `run-local.sh` script that runs the install/migrate/start steps, and
* Produce a `requirements.txt` exported from your `pyproject.toml`.

Tell me which of these I should do next.







app/
└── common/
    ├── __init__.py
    │
    ├── db/
    │    ├── base_model.py
    │    ├── base_schema.py
    │    ├── base_service.py
    │    ├── repository.py
    │    └── mixins/
    │          ├── timestamp_mixin.py
    │          ├── soft_delete_mixin.py
    │          └── uuid_mixin.py
    │
    ├── utils/
    │    ├── hashing.py
    │    ├── jwt.py
    │    ├── datetime.py
    │    ├── strings.py
    │    └── validation.py
    │
    ├── decorators/
    │    ├── cache.py
    │    ├── roles.py
    │    ├── rate_limit.py
    │    └── trace.py
    │
    ├── enums/
    │    ├── status.py
    │    └── roles.py
    │
    └── dto/
         ├── pagination.py
         └── response.py





YOUR NOVAKIT LAYERS (Final Clean Mapping)
1. ORM Model = Yii2 ActiveRecord
app/modules/iam/models/user.py

2. Repository = Custom layer (Yii2 doesn't have this)
app/modules/iam/repositories/user_repository.py


This is optional—Yii2 does not use repositories.

3. Service Layer = Yii2 model logic
app/modules/iam/services/user_service.py


This represents Yii2 methods like:

setPassword()

validatePassword()

generateAuthKey()

generateJWT()

afterSave()

updatePasswordHistory()

4. Controller = Yii2 Controllers
app/modules/iam/controllers/auth_controller.py (example)

5. Schemas = Yii2 has no equivalent
UserCreate, UserOut


These are FastAPI DTOs.