import pytest
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.db.session import get_db_session
from app.models.category import Category
from app.models.tag import Tag, KnowledgeTag
from app.models.knowledge import KnowledgeItem
from app.models.source import KnowledgeSource
from app.models.embedding import EmbeddingChunk


@pytest.fixture
async def test_db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Category.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(KnowledgeItem.__table__.create)
        await conn.run_sync(KnowledgeTag.__table__.create)
        await conn.run_sync(KnowledgeSource.__table__.create)
        await conn.run_sync(EmbeddingChunk.__table__.create)

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_get_db

    yield session_factory

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_knowledge_crud_lifecycle(test_db_session):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Setup Category and Tag
        cat_res = await client.post("/api/categories", json={"name": "技术类"})
        cat_id = cat_res.json()["id"]

        tag_res = await client.post("/api/tags", json={"name": "FastAPI"})
        tag_id = tag_res.json()["id"]

        # 2. Create Knowledge Item with blocks, category, tags and sources
        create_payload = {
            "title": "FastAPI 异步架构与性能实践",
            "summary": "详细解析 FastAPI 与 asyncpg 的高性能配置",
            "category_id": cat_id,
            "tag_ids": [tag_id],
            "blocks_json": [
                {"type": "heading", "content": "FastAPI 核心概念", "properties": {"level": 1}},
                {"type": "paragraph", "content": "FastAPI 基于 Starlette 与 Pydantic 构建。"},
                {"type": "code", "content": "app = FastAPI()", "properties": {"language": "python"}},
            ],
            "source_type": "ai_search",
            "status": "published",
            "favorite": True,
            "sources": [
                {
                    "type": "url",
                    "url": "https://fastapi.tiangolo.com",
                    "title": "FastAPI Official Documentation",
                    "metadata_json": {"author": "tiangolo"},
                }
            ],
        }

        resp = await client.post("/api/knowledge", json=create_payload)
        assert resp.status_code == 201
        data = resp.json()

        k_id = data["id"]
        assert data["title"] == "FastAPI 异步架构与性能实践"
        assert data["category_name"] == "技术类"
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "FastAPI"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["title"] == "FastAPI Official Documentation"

        # Verify plain_text derivation
        assert "FastAPI 核心概念" in data["plain_text"]
        assert "app = FastAPI()" in data["plain_text"]

        # 3. Retrieve Detail
        detail_resp = await client.get(f"/api/knowledge/{k_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["id"] == k_id

        # 4. List & Filter
        list_resp = await client.get(f"/api/knowledge?category_id={cat_id}")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 1

        # 5. Update Knowledge (change blocks)
        update_payload = {
            "title": "FastAPI 异步架构实践（修订版）",
            "blocks_json": [
                {"type": "paragraph", "content": "修订后的正文内容。"},
            ],
        }
        up_resp = await client.put(f"/api/knowledge/{k_id}", json=update_payload)
        assert up_resp.status_code == 200
        up_data = up_resp.json()
        assert up_data["title"] == "FastAPI 异步架构实践（修订版）"
        assert up_data["plain_text"] == "修订后的正文内容。"
        assert up_data["index_status"] == "pending"

        # 6. Move to Trash (Soft delete)
        del_resp = await client.delete(f"/api/knowledge/{k_id}")
        assert del_resp.status_code == 204

        # Verify excluded from normal list
        normal_list = await client.get("/api/knowledge")
        assert normal_list.json()["total"] == 0

        # Verify present in trash list
        trash_list = await client.get("/api/knowledge/trash/list")
        assert trash_list.json()["total"] == 1
        assert trash_list.json()["items"][0]["id"] == k_id

        # 7. Restore from Trash
        restore_resp = await client.post(f"/api/knowledge/{k_id}/restore")
        assert restore_resp.status_code == 200

        # Verify back in normal list
        restored_list = await client.get("/api/knowledge")
        assert restored_list.json()["total"] == 1

        # 8. Permanent Delete
        perm_resp = await client.delete(f"/api/knowledge/{k_id}/permanent")
        assert perm_resp.status_code == 204

        # Verify totally gone
        final_check = await client.get(f"/api/knowledge/{k_id}")
        assert final_check.status_code == 404
