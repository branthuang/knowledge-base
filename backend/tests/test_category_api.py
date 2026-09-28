import pytest
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.main import app
from app.db.session import Base, get_db_session
from app.models.category import Category
from app.models.knowledge import KnowledgeItem
from app.services.category_service import get_cascade_category_ids


@pytest.fixture
async def test_db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Category.__table__.create)
        await conn.run_sync(KnowledgeItem.__table__.create)

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_get_db

    yield session_factory

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_category_crud_and_tree(test_db_session):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create parent category
        resp1 = await client.post(
            "/api/categories",
            json={"name": "技术类", "description": "所有技术文档", "icon": "code", "sort_order": 1},
        )
        assert resp1.status_code == 201
        parent = resp1.json()
        assert parent["name"] == "技术类"

        # 2. Create child category
        resp2 = await client.post(
            "/api/categories",
            json={"name": "Shopify", "parent_id": parent["id"], "sort_order": 1},
        )
        assert resp2.status_code == 201
        child = resp2.json()
        assert child["parent_id"] == parent["id"]

        # 3. Retrieve category tree
        tree_resp = await client.get("/api/categories/tree")
        assert tree_resp.status_code == 200
        tree = tree_resp.json()
        assert len(tree) == 1
        assert tree[0]["id"] == parent["id"]
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["id"] == child["id"]

        # 4. Test cascade IDs logic directly
        async with test_db_session() as session:
            cascade_ids = await get_cascade_category_ids(session, parent["id"])
            assert parent["id"] in cascade_ids
            assert child["id"] in cascade_ids

        # 5. Update category
        update_resp = await client.put(f"/api/categories/{child['id']}", json={"color": "#10B981"})
        assert update_resp.status_code == 200
        assert update_resp.json()["color"] == "#10B981"


@pytest.mark.asyncio
async def test_category_deletion_guard(test_db_session):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create category
        c_resp = await client.post("/api/categories", json={"name": "待删除分类"})
        cat_id = c_resp.json()["id"]

        # 2. Add a knowledge item associated with this category
        async with test_db_session() as session:
            k = KnowledgeItem(title="关联知识测试", category_id=cat_id, blocks_json=[])
            session.add(k)
            await session.commit()
            k_id = k.id

        # 3. Attempt delete without reassign -> Must return 400
        del_fail = await client.delete(f"/api/categories/{cat_id}")
        assert del_fail.status_code == 400
        assert "无法直接删除" in del_fail.json()["detail"]

        # 4. Delete with reassign_to_id="unclassified" -> Must succeed
        del_ok = await client.delete(f"/api/categories/{cat_id}?reassign_to_id=unclassified")
        assert del_ok.status_code == 204

        # 5. Verify knowledge item has category_id=None
        async with test_db_session() as session:
            result = await session.execute(select(KnowledgeItem).where(KnowledgeItem.id == k_id))
            item = result.scalar_one()
            assert item.category_id is None
