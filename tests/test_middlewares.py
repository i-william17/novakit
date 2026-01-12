import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from app.core.middlewares.request_id import RequestIDMiddleware
from app.core.middlewares.process_time import ProcessTimeMiddleware
from app.core.middlewares.maintenance_mode import MaintenanceModeMiddleware
from config.config import settings

@pytest.fixture
def app():
    app = FastAPI()
    # apply middlewares
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(ProcessTimeMiddleware)
    yield app

def test_request_id_and_process_time_headers(app):
    @app.get("/ping")
    async def ping():
        return {"ok": True}

    client = TestClient(app)
    r = client.get("/ping")
    assert r.status_code == 200
    assert "X-Request-ID" in r.headers
    assert "X-Process-Time" in r.headers

@pytest.mark.asyncio
async def test_maintenance_mode(monkeypatch):
    from fastapi import FastAPI
    app = FastAPI()
    # toggle maintenance on
    monkeypatch.setattr(settings, "MAINTENANCE_MODE", True)
    app.add_middleware(MaintenanceModeMiddleware)

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    client = TestClient(app)
    r = client.get("/ping")
    assert r.status_code == 503
    monkeypatch.setattr(settings, "MAINTENANCE_MODE", False)
