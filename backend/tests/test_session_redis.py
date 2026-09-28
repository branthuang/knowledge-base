import pytest
from sqlalchemy import text
from app.db.session import get_engine, check_db_health, AsyncSessionLocal
from app.core.redis import check_redis_health, close_redis, get_redis_client


@pytest.mark.asyncio
async def test_async_engine_sqlite_in_memory():
    test_engine = get_engine("sqlite+aiosqlite:///:memory:")
    assert test_engine is not None
    async with test_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_db_health_check_failure_handled():
    # Calling check_db_health against an offline db port returns False instead of raising an unhandled exception
    is_healthy = await check_db_health()
    # It returns boolean (True if local docker PG is running, False if not yet started)
    assert isinstance(is_healthy, bool)


@pytest.mark.asyncio
async def test_redis_health_and_lifecycle():
    client = get_redis_client()
    assert client is not None
    # If redis is not running, check_redis_health should safely return False without crashing
    health = await check_redis_health()
    assert isinstance(health, bool)
    await close_redis()
