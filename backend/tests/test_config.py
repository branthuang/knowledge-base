import os
from app.core.config import Settings, get_settings


def test_default_settings():
    settings = Settings()
    assert settings.APP_NAME == "knowledge-base"
    assert settings.DEBUG is True
    assert settings.API_PREFIX == "/api"
    assert "postgresql" in settings.DATABASE_URL
    assert "redis" in settings.REDIS_URL
    assert settings.EMBEDDING_DIMENSIONS == 1536


def test_settings_env_override(monkeypatch):
    monkeypatch.setenv("APP_NAME", "my-kb")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "768")

    settings = Settings()
    assert settings.APP_NAME == "my-kb"
    assert settings.DEBUG is False
    assert settings.EMBEDDING_DIMENSIONS == 768


def test_get_settings_cached():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
