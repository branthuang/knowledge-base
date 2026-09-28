import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.models.category import Category
from app.db.seed import seed_default_categories


@pytest.mark.asyncio
async def test_seed_default_categories_idempotency():
    # Use SQLite in-memory for testing seed logic
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        # Create only the categories table for seed testing
        await conn.run_sync(Category.__table__.create)

    # First seeding
    async with session_factory() as session:
        cats = await seed_default_categories(session)
        assert len(cats) == 2
        names = [c.name for c in cats]
        assert "技术类" in names
        assert "公司知识类" in names

    # Verify rows in database
    async with session_factory() as session:
        result = await session.execute(select(Category))
        all_cats = result.scalars().all()
        assert len(all_cats) == 2

    # Second seeding (idempotency check)
    async with session_factory() as session:
        cats_second = await seed_default_categories(session)
        assert len(cats_second) == 2

    # Verify still exactly 2 rows
    async with session_factory() as session:
        result = await session.execute(select(Category))
        all_cats = result.scalars().all()
        assert len(all_cats) == 2

    await engine.dispose()
