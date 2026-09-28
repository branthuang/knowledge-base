import pytest
import httpx
from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Welcome to knowledge-base API" in data["message"]
        assert data["docs_url"] == "/docs"


@pytest.mark.asyncio
async def test_health_check_healthy(monkeypatch):
    async def mock_db_true():
        return True

    async def mock_redis_true():
        return True

    monkeypatch.setattr("app.api.health.check_db_health", mock_db_true)
    monkeypatch.setattr("app.api.health.check_redis_health", mock_redis_true)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["database"] == "connected"
        assert data["services"]["redis"] == "connected"


@pytest.mark.asyncio
async def test_health_check_degraded(monkeypatch):
    async def mock_db_false():
        return False

    async def mock_redis_false():
        return False

    monkeypatch.setattr("app.api.health.check_db_health", mock_db_false)
    monkeypatch.setattr("app.api.health.check_redis_health", mock_redis_false)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["database"] == "disconnected"
        assert data["services"]["redis"] == "disconnected"
