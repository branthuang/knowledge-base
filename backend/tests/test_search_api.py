import pytest
import httpx
from typing import List
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.db.session import get_db_session
from app.core.config import settings
from app.models.category import Category
from app.models.tag import Tag, KnowledgeTag
from app.models.knowledge import KnowledgeItem
from app.models.source import KnowledgeSource
from app.models.embedding import EmbeddingChunk
from app.providers.base import BaseEmbeddingProvider, EmbeddingResponse
from app.services.index_service import IndexService
from app.services.search_service import HybridSearchService
from app.api import search as search_api_module


class DeterministicMockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Mock embedding provider that generates predictable vectors:
    - If keyword 'python' or 'fastapi' appears, returns a vector with high activation in component 0.
    - If keyword 'react' appears, returns a vector with high activation in component 1.
    - Otherwise returns standard uniform vector.
    """
    def __init__(self, dimensions: int = settings.EMBEDDING_DIMENSIONS):
        self.dimensions = dimensions

    async def embed_texts(self, texts: List[str]) -> EmbeddingResponse:
        embeddings = []
        for text in texts:
            t_low = text.lower()
            vec = [0.01] * self.dimensions
            if "python" in t_low or "fastapi" in t_low:
                vec[0] = 0.95
                vec[1] = 0.05
            elif "react" in t_low or "nextjs" in t_low:
                vec[0] = 0.05
                vec[1] = 0.95
            else:
                vec[0] = 0.2
                vec[1] = 0.2
            embeddings.append(vec)

        return EmbeddingResponse(
            embeddings=embeddings,
            model="mock-deterministic",
            dimensions=self.dimensions,
            total_tokens=sum(len(t) for t in texts),
        )

    async def check_connectivity(self) -> bool:
        return True


@pytest.fixture
async def search_test_context():
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

    # Inject mock provider into services
    mock_provider = DeterministicMockEmbeddingProvider()
    custom_index_service = IndexService(embedding_provider=mock_provider)
    custom_search_service = HybridSearchService(embedding_provider=mock_provider)

    original_search_svc = search_api_module.default_search_service
    original_index_svc = search_api_module.default_index_service
    search_api_module.default_search_service = custom_search_service
    search_api_module.default_index_service = custom_index_service

    # Seed baseline knowledge data
    async with session_factory() as session:
        # Categories: Root "技术类", Child "后端", Child "前端"
        cat_tech = Category(id="cat-tech", name="技术类", sort_order=1)
        cat_backend = Category(id="cat-backend", name="后端", parent_id="cat-tech", sort_order=2)
        cat_frontend = Category(id="cat-frontend", name="前端", parent_id="cat-tech", sort_order=3)
        session.add_all([cat_tech, cat_backend, cat_frontend])

        # Tags
        tag_fastapi = Tag(id="tag-fastapi", name="FastAPI", color="#009688")
        tag_react = Tag(id="tag-react", name="React", color="#61dafb")
        session.add_all([tag_fastapi, tag_react])
        await session.commit()

        # Knowledge 1: FastAPI (in cat-backend, tag-fastapi)
        k1 = KnowledgeItem(
            id="k-fastapi",
            title="FastAPI 高并发架构设计",
            summary="深入理解 FastAPI 的异步事件循环与依赖注入机制",
            blocks_json=[
                {"id": "b-f1", "type": "heading", "content": "FastAPI 异步架构", "properties": {"level": 1}},
                {"id": "b-f2", "type": "paragraph", "content": "FastAPI 使用 Python 的 asyncio 实现高效高并发处理。"},
            ],
            plain_text="# FastAPI 异步架构\n\nFastAPI 使用 Python 的 asyncio 实现高效高并发处理。",
            category_id="cat-backend",
            source_type="manual",
            status="published",
            favorite=True,
        )
        session.add(k1)
        session.add(KnowledgeTag(knowledge_id=k1.id, tag_id=tag_fastapi.id))

        # Knowledge 2: React (in cat-frontend, tag-react)
        k2 = KnowledgeItem(
            id="k-react",
            title="React 18 并发渲染与 Hooks 深度解析",
            summary="React 18 Fiber 架构以及并发渲染特性的完整指南",
            blocks_json=[
                {"id": "b-r1", "type": "heading", "content": "React 18 并发模式", "properties": {"level": 1}},
                {"id": "b-r2", "type": "paragraph", "content": "并发渲染让 React 能够同时准备多个版本的 UI。"},
            ],
            plain_text="# React 18 并发模式\n\n并发渲染让 React 能够同时准备多个版本的 UI。",
            category_id="cat-frontend",
            source_type="manual",
            status="published",
            favorite=False,
        )
        session.add(k2)
        session.add(KnowledgeTag(knowledge_id=k2.id, tag_id=tag_react.id))

        # Knowledge 3: Soft-deleted (trashed) item
        k3 = KnowledgeItem(
            id="k-trashed",
            title="废弃的 Python 笔记",
            plain_text="已经被移入回收站的过期内容",
            category_id="cat-backend",
            status="trashed",
        )
        session.add(k3)

        await session.commit()

        # Index k1 and k2
        await custom_index_service.index_knowledge_item(session, k1)
        await custom_index_service.index_knowledge_item(session, k2)

    yield {
        "session_factory": session_factory,
        "mock_provider": mock_provider,
        "cat_tech_id": "cat-tech",
        "cat_backend_id": "cat-backend",
        "tag_fastapi_id": "tag-fastapi",
    }

    # Teardown
    search_api_module.default_search_service = original_search_svc
    search_api_module.default_index_service = original_index_svc
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_search_sufficient_hit(search_test_context):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Search query matching FastAPI exactly in title and vector
        response = await client.post("/api/search", json={"query": "FastAPI 高并发架构设计"})
        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 1
        assert data["is_sufficient"] is True
        assert data["ai_search_suggested"] is False
        assert data["ai_search_prompt"] is None

        top_hit = data["items"][0]
        assert top_hit["id"] == "k-fastapi"
        assert top_hit["title"] == "FastAPI 高并发架构设计"
        assert top_hit["score"] >= 0.60
        assert top_hit["keyword_score"] > 0.0
        assert top_hit["vector_score"] > 0.0
        assert "FastAPI" in top_hit["best_snippet"]
        assert top_hit["matched_block_id"] is not None
        assert len(top_hit["tags"]) == 1
        assert top_hit["tags"][0]["name"] == "FastAPI"


@pytest.mark.asyncio
async def test_search_insufficient_hit_and_ai_guidance(search_test_context):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Unrelated query or query yielding low scores
        response = await client.post(
            "/api/search",
            json={"query": "量子力学与广义相对论大一统理论", "minimum_score": 0.60},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["is_sufficient"] is False
        assert data["ai_search_suggested"] is True
        assert "AI 搜索" in data["ai_search_prompt"]


@pytest.mark.asyncio
async def test_search_cascade_category_filtering(search_test_context):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Search with parent category "cat-tech" -> should return both Backend (FastAPI) and Frontend (React)
        res_parent = await client.post(
            "/api/search",
            json={"query": "架构", "category_id": "cat-tech"},
        )
        assert res_parent.status_code == 200
        items_parent = res_parent.json()["items"]
        parent_ids = [item["id"] for item in items_parent]
        assert "k-fastapi" in parent_ids

        # 2. Search with subcategory "cat-backend" -> should return k-fastapi, NOT k-react
        res_sub = await client.post(
            "/api/search",
            json={"query": "架构", "category_id": "cat-backend"},
        )
        assert res_sub.status_code == 200
        items_sub = res_sub.json()["items"]
        sub_ids = [item["id"] for item in items_sub]
        assert "k-fastapi" in sub_ids
        assert "k-react" not in sub_ids


@pytest.mark.asyncio
async def test_search_tag_filtering(search_test_context):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Filter by tag-fastapi
        res = await client.post(
            "/api/search",
            json={"query": "并发", "tag_ids": ["tag-fastapi"]},
        )
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["id"] == "k-fastapi"


@pytest.mark.asyncio
async def test_search_get_endpoint_and_pagination(search_test_context):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/search", params={"q": "FastAPI", "page": 1, "page_size": 1})
        assert res.status_code == 200
        data = res.json()
        assert data["page"] == 1
        assert data["page_size"] == 1
        assert len(data["items"]) <= 1


@pytest.mark.asyncio
async def test_search_excludes_trashed_items(search_test_context):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/search", json={"query": "废弃的 Python 笔记"})
        assert res.status_code == 200
        data = res.json()
        # Trashed item k-trashed must not be returned
        item_ids = [item["id"] for item in data["items"]]
        assert "k-trashed" not in item_ids


@pytest.mark.asyncio
async def test_search_reindex_endpoint(search_test_context):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/search/reindex")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["metrics"]["total_items"] >= 2
        assert data["metrics"]["successful_items"] >= 2
