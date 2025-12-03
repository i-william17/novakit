# 🚀 Novakit FastAPI Boilerplate

<a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/fastapi/full-stack-fastapi-template" target="_blank"><img src="https://coverage-badge.samuelcolvin.workers.dev/fastapi/full-stack-fastapi-template.svg" alt="Coverage"></a>


 Welcome to **NovaKit**, a production‑ready backend boilerplate built with **FastAPI**, **SQLAlchemy**, **Alembic**, **Pydantic**, and **Poetry**. This template provides a clean, scalable foundation for modern backend systems.
## Technology Stack and Features

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
    - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
    - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
    - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
- 🐋 [Docker Compose](https://www.docker.com) for development and production.
- 🔒 Secure password hashing by default.
- 🔑 JWT (JSON Web Token) authentication.
- 📫 Email based password recovery.
- ✅ Tests with [Pytest](https://pytest.org).
- 📞 [Traefik](https://traefik.io) as a reverse proxy / load balancer.
- 🚢 Deployment instructions using Docker Compose, including how to set up a frontend Traefik proxy to handle automatic HTTPS certificates.
- 🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.

# 📁 Project Structure
```bash
comming soon 
```
 
## 🚀 Getting Started

You can **just fork or clone** this repository and use it as is.

✨ It just works. ✨

### How to Use a Private Repository

```bash
git clone https://github.com/Francis-Yuppie/novakit.git
```

- Enter into the new directory:

```bash
cd novakit
```

- Set the new origin to your new repository, copy it from the GitHub interface, for example:

```bash
git remote set-url origin https://github.com/Francis-Yuppie/novakit.git
```

- Add this repo as another "remote" to allow you to get updates later:

```bash
git remote add upstream https://github.com/Francis-Yuppie/novakit.git
```

- Push the code to your new repository:

```bash
git push -u origin master
```
 

- Pull the latest changes without merging:

```bash
git pull --no-commit upstream master
```

This will download the latest changes from this template without committing them, that way you can check everything is right before committing.

- If there are conflicts, solve them in your editor.

- Once you are done, commit the changes:

```bash
git merge --continue
```

### Install dependencies

```bash
poetry install
```

### Configure

You can then update configs in the `.env` files to customize your configurations.

Before deploying it, make sure you change at least the values for:

- `SECRET_KEY`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_PASSWORD`

You can (and should) pass these as environment variables from secrets.

Read the [deployment.md](./deployment.md) docs for more details.

### Generate Secret Keys

Some environment variables in the `.env` file have a default value of `changethis`.

You have to change them with a secret key, to generate secret keys you can run the following command:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the content and use that as password / secret key. And run that again to generate another secure key.

## Database Setup
### Initialize the DB (first‑time)

```bash
poetry run alembic upgrade head
```

### If DB is empty and migration history missing:
```bash
poetry run alembic stamp head
```
## Alembic Migration Guide

### Create autogenerate migration

```bash
poetry run alembic revision --autogenerate -m "message"
```

### Create manual/empty migration
```bash
poetry run alembic revision -m "message"
```

## Apply migrations
```bash
poetry run alembic upgrade head
```

# Running the App
### Start development server
```bash
 poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
### Production (Gunicorn + Uvicorn workers)
```bash
gunicorn -k uvicorn.workers.UvicornWorker app.main:app
```
## Deployment

Deployment docs: [deployment.md](./deployment.md).

## Development

General development docs: [development.md](./development.md).

This includes using Docker Compose, custom local domains, `.env` configurations, etc.

## Release Notes

Check the file [release-notes.md](./release-notes.md).

## License

The Full Stack FastAPI Template is licensed under the terms of the MIT license.
