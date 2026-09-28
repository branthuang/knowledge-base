import pytest
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.main import app
from app.db.session import get_db_session
from app.models.tag import Tag, KnowledgeTag
from app.models.knowledge import KnowledgeItem


@pytest.fixture
async def test_db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(KnowledgeItem.__table__.create)
        await conn.run_sync(KnowledgeTag.__table__.create)

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_get_db

    yield session_factory

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_tag_crud(test_db_session):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create tag
        create_res = await client.post(
            "/api/tags",
            json={"name": "Shopify", "description": "Shopify 生态相关", "color": "#008060"},
        )
        assert create_res.status_code == 201
        tag = create_res.json()
        assert tag["name"] == "Shopify"
        tag_id = tag["id"]

        # 2. Attempt duplicate tag name -> 400
        dup_res = await client.post("/api/tags", json={"name": "Shopify"})
        assert dup_res.status_code == 400
        assert "已存在同名标签" in dup_res.json()["detail"]

        # 3. List tags
        list_res = await client.get("/api/tags")
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) == 1
        assert items[0]["id"] == tag_id
        assert items[0]["knowledge_count"] == 0

        # 4. Update tag
        up_res = await client.put(f"/api/tags/{tag_id}", json={"color": "#000000"})
        assert up_res.status_code == 200
        assert up_res.json()["color"] == "#000000"

        # 5. Delete tag
        del_res = await client.delete(f"/api/tags/{tag_id}")
        assert del_res.status_code == 204

        # 6. Verify deleted
        get_res = await client.get(f"/api/tags/{tag_id}")
        assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_tag_merge_transaction(test_db_session):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Tag A (source) and Tag B (target)
        r_a = await client.post("/api/tags", json={"name": "CDN_Old"})
        tag_a_id = r_a.json()["id"]

        r_b = await client.post("/api/tags", json={"name": "CDN"})
        tag_b_id = r_b.json()["id"]

        # In DB, create 3 knowledge items and bind:
        # Item 1: bound to Tag A only
        # Item 2: bound to BOTH Tag A and Tag B (collision check!)
        # Item 3: bound to Tag B only
        async with test_db_session() as session:
            k1 = KnowledgeItem(id="k1", title="Doc 1", blocks_json=[])
            k2 = KnowledgeItem(id="k2", title="Doc 2", blocks_json=[])
            k3 = KnowledgeItem(id="k3", title="Doc 3", blocks_json=[])
            session.add_all([k1, k2, k3])

            link1 = KnowledgeTag(knowledge_id="k1", tag_id=tag_a_id)
            link2_a = KnowledgeTag(knowledge_id="k2", tag_id=tag_a_id)
            link2_b = KnowledgeTag(knowledge_id="k2", tag_id=tag_b_id)
            link3 = KnowledgeTag(knowledge_id="k3", tag_id=tag_b_id)
            session.add_all([link1, link2_a, link2_b, link3])
            await session.commit()

        # Merge Tag A into Tag B
        merge_res = await client.post(
            "/api/tags/merge",
            json={"source_tag_id": tag_a_id, "target_tag_id": tag_b_id},
        )
        assert merge_res.status_code == 200
        assert merge_res.json()["name"] == "CDN"

        # Verify Tag A is gone
        check_a = await client.get(f"/api/tags/{tag_a_id}")
        assert check_a.status_code == 404

        # Check stats on Tag B -> must be linked to 3 knowledge items (k1, k2, k3)
        list_res = await client.get("/api/tags")
        items = [t for t in list_res.json() if t["id"] == tag_b_id]
        assert len(items) == 1
        assert items[0]["knowledge_count"] == 3
