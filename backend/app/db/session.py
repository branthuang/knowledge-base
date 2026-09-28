from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def get_engine(db_url: str = None) -> AsyncEngine:
    """Create and configure asynchronous database engine."""
    url = db_url or settings.DATABASE_URL
    # For SQLite async testing vs PostgreSQL connection pool arguments
    connect_args = {}
    pool_kwargs = {}
    if "sqlite" in url:
        connect_args["check_same_thread"] = False
    else:
        pool_kwargs = {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
        }

    return create_async_engine(
        url,
        echo=settings.DEBUG,
        connect_args=connect_args,
        **pool_kwargs,
    )


engine = get_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing request-scoped async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    """Perform database connectivity health check."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False
