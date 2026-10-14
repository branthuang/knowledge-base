import pytest
from typing import List, Optional, Any
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.category import Category
from app.models.tag import Tag, KnowledgeTag
from app.models.knowledge import KnowledgeItem
from app.models.source import KnowledgeSource
from app.models.embedding import EmbeddingChunk
from app.models.search_session import SearchSession
from app.providers.base import (
    BaseLLMProvider,
    BaseSearchProvider,
    BaseEmbeddingProvider,
    LLMMessage,
    LLMResponse,
    SearchResult,
    SearchCitation,
    EmbeddingResponse,
)
from app.schemas.ai_search import SearchMode, AISearchRequest
from app.services.chunker import default_chunker
from app.services.index_service import IndexService
from app.services.search_service import HybridSearchService
from app.services.ai_search_service import AISearchService


class MockLLM(BaseLLMProvider):
    def __init__(self):
        self.call_count = 0
        self.last_messages: List[LLMMessage] = []

    async def chat_complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> LLMResponse:
        self.call_count += 1
        self.last_messages = messages
        return LLMResponse(
            content=f"这是基于参考信息生成的 AI 回答。已处理 {len(messages)} 条上下文。",
            model="mock-gpt-4o",
            usage={"total_tokens": 128},
        )

    async def check_connectivity(self) -> bool:
        return True


class MockSearch(BaseSearchProvider):
    def __init__(self):
        self.call_count = 0

    async def search(self, query: str, max_results: int = 5) -> SearchResult:
        self.call_count += 1
        return SearchResult(
            query=query,
            citations=[
                SearchCitation(
                    title="公网参考 1: 异步框架对比",
                    url="https://example.com/async-frameworks",
                    snippet="FastAPI 相比传统框架在 I/O 密集型场景具备显著优势。",
                    source_name="example.com",
                ),
                SearchCitation(
                    title="公网参考 2: Python 3.12 性能提升",
                    url="https://example.com/python-perf",
                    snippet="Python 3.12 针对 asyncio 事件循环进行了底层优化。",
                    source_name="example.com",
                ),
            ],
            raw_answer="公网摘要",
        )

    async def check_connectivity(self) -> bool:
        return True


class MockEmbedding(BaseEmbeddingProvider):
    async def embed_texts(self, texts: List[str]) -> EmbeddingResponse:
        dim = 1536
        embeddings = []
        for t in texts:
            vec = [0.1] * dim
            if "fastapi" in t.lower():
                vec[0] = 0.99
            embeddings.append(vec)
        return EmbeddingResponse(
            embeddings=embeddings,
            model="mock-embed",
            dimensions=dim,
            total_tokens=sum(len(t) for t in texts),
        )

    async def check_connectivity(self) -> bool:
        return True


@pytest.fixture
async def ai_search_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Category.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(KnowledgeItem.__table__.create)
        await conn.run_sync(KnowledgeTag.__table__.create)
        await conn.run_sync(KnowledgeSource.__table__.create)
        await conn.run_sync(EmbeddingChunk.__table__.create)
        await conn.run_sync(SearchSession.__table__.create)

    # Seed baseline item
    async with session_factory() as session:
        k = KnowledgeItem(
            id="k-fastapi-doc",
            title="FastAPI 生产部署指南",
            plain_text="FastAPI 在生产环境通常配合 Uvicorn 和 Gunicorn 多进程部署。",
            status="published",
        )
        session.add(k)
        await session.commit()

        # Index item
        index_svc = IndexService(embedding_provider=MockEmbedding())
        await index_svc.index_knowledge_item(session, k)

    yield session_factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_knowledge_only_mode_with_hit(ai_search_db):
    mock_llm = MockLLM()
    mock_search = MockSearch()
    search_svc = HybridSearchService(embedding_provider=MockEmbedding())
    ai_svc = AISearchService(
        llm_provider=mock_llm,
        search_provider=mock_search,
        hybrid_search_svc=search_svc,
    )

    async with ai_search_db() as session:
        req = AISearchRequest(
            query="FastAPI 生产部署指南",
            mode=SearchMode.KNOWLEDGE_ONLY,
            minimum_score=0.50,
        )
        resp = await ai_svc.execute_ai_search(session, req)

        assert resp.mode == SearchMode.KNOWLEDGE_ONLY
        assert resp.is_sufficient is True
        assert len(resp.local_hits) >= 1
        assert len(resp.citations) == 0  # Knowledge only must not produce external citations
        assert mock_search.call_count == 0  # External search must NOT be called
        assert mock_llm.call_count == 1
        assert "仅知识库" in mock_llm.last_messages[0].content


@pytest.mark.asyncio
async def test_knowledge_only_mode_insufficient(ai_search_db):
    mock_llm = MockLLM()
    mock_search = MockSearch()
    search_svc = HybridSearchService(embedding_provider=MockEmbedding())
    ai_svc = AISearchService(
        llm_provider=mock_llm,
        search_provider=mock_search,
        hybrid_search_svc=search_svc,
    )

    async with ai_search_db() as session:
        req = AISearchRequest(
            query="完全不存在的火星生物学理论",
            mode=SearchMode.KNOWLEDGE_ONLY,
            minimum_score=0.60,
        )
        resp = await ai_svc.execute_ai_search(session, req)

        assert resp.mode == SearchMode.KNOWLEDGE_ONLY
        assert resp.is_sufficient is False
        assert mock_search.call_count == 0
        assert mock_llm.call_count == 0  # No LLM call when insufficient in knowledge_only
        assert "未检索到" in resp.ai_answer


@pytest.mark.asyncio
async def test_knowledge_first_mode_sufficient(ai_search_db):
    mock_llm = MockLLM()
    mock_search = MockSearch()
    search_svc = HybridSearchService(embedding_provider=MockEmbedding())
    ai_svc = AISearchService(
        llm_provider=mock_llm,
        search_provider=mock_search,
        hybrid_search_svc=search_svc,
    )

    async with ai_search_db() as session:
        req = AISearchRequest(
            query="FastAPI 生产部署指南",
            mode=SearchMode.KNOWLEDGE_FIRST,
            minimum_score=0.50,
        )
        resp = await ai_svc.execute_ai_search(session, req)

        assert resp.is_sufficient is True
        assert len(resp.local_hits) >= 1
        assert len(resp.citations) == 0
        assert mock_search.call_count == 0  # Sufficient locally, no external search needed
        assert mock_llm.call_count == 1


@pytest.mark.asyncio
async def test_knowledge_first_mode_insufficient_triggers_external(ai_search_db):
    mock_llm = MockLLM()
    mock_search = MockSearch()
    search_svc = HybridSearchService(embedding_provider=MockEmbedding())
    ai_svc = AISearchService(
        llm_provider=mock_llm,
        search_provider=mock_search,
        hybrid_search_svc=search_svc,
    )

    async with ai_search_db() as session:
        req = AISearchRequest(
            query="Kubernetes Pod 资源调度算法",
            mode=SearchMode.KNOWLEDGE_FIRST,
            minimum_score=0.60,
        )
        resp = await ai_svc.execute_ai_search(session, req)

        assert resp.is_sufficient is False
        assert mock_search.call_count == 1  # Insufficient locally -> triggers external search
        assert len(resp.citations) == 2
        assert mock_llm.call_count == 1


@pytest.mark.asyncio
async def test_search_session_persistence_and_retrieval(ai_search_db):
    mock_llm = MockLLM()
    mock_search = MockSearch()
    search_svc = HybridSearchService(embedding_provider=MockEmbedding())
    ai_svc = AISearchService(
        llm_provider=mock_llm,
        search_provider=mock_search,
        hybrid_search_svc=search_svc,
    )

    async with ai_search_db() as session:
        req = AISearchRequest(
            query="Direct AI Search Query",
            mode=SearchMode.DIRECT_AI,
        )
        resp = await ai_svc.execute_ai_search(session, req)

        # Retrieve session list
        sessions = await ai_svc.list_sessions(session)
        assert len(sessions) == 1
        assert sessions[0].id == resp.session_id
        assert sessions[0].query == "Direct AI Search Query"

        # Retrieve single session detail
        detail = await ai_svc.get_session(session, resp.session_id)
        assert detail is not None
        assert detail.id == resp.session_id
        assert detail.mode == "direct_ai"
        assert len(detail.citations_json) == 2


@pytest.mark.asyncio
async def test_ai_search_http_endpoints(ai_search_db):
    import httpx
    from app.main import app
    from app.db.session import get_db_session
    from app.api import ai_search as ai_search_api_module

    session_factory = ai_search_db
    async def _override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_db

    mock_llm = MockLLM()
    mock_search = MockSearch()
    search_svc = HybridSearchService(embedding_provider=MockEmbedding())
    custom_ai_svc = AISearchService(
        llm_provider=mock_llm,
        search_provider=mock_search,
        hybrid_search_svc=search_svc,
    )
    original_svc = ai_search_api_module.default_ai_search_service
    ai_search_api_module.default_ai_search_service = custom_ai_svc

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. POST /api/ai-search
            post_res = await client.post(
                "/api/ai-search",
                json={"query": "FastAPI 生产部署指南", "mode": "knowledge_first", "minimum_score": 0.50},
            )
            assert post_res.status_code == 200
            post_data = post_res.json()
            sess_id = post_data["session_id"]
            assert post_data["is_sufficient"] is True

            # 2. GET /api/ai-search/sessions
            list_res = await client.get("/api/ai-search/sessions")
            assert list_res.status_code == 200
            list_data = list_res.json()
            assert len(list_data) >= 1
            assert list_data[0]["id"] == sess_id

            # 3. GET /api/ai-search/sessions/{sess_id}
            detail_res = await client.get(f"/api/ai-search/sessions/{sess_id}")
            assert detail_res.status_code == 200
            detail_data = detail_res.json()
            assert detail_data["id"] == sess_id
            assert detail_data["query"] == "FastAPI 生产部署指南"
    finally:
        ai_search_api_module.default_ai_search_service = original_svc
        app.dependency_overrides.clear()


def test_default_providers_and_settings():
    """Verify that default provider initializers read configuration without AttributeError."""
    from app.services.ai_search_service import get_default_llm_provider, get_default_search_provider
    from app.services.optimization_service import get_default_llm_provider as get_opt_llm_provider
    from app.core.config import settings

    # Check Settings properties
    assert settings.LLM_MODEL
    assert settings.LLM_MODEL_NAME == settings.LLM_MODEL

    # Check default provider creation
    llm = get_default_llm_provider()
    assert llm.model == settings.LLM_MODEL

    opt_llm = get_opt_llm_provider()
    assert opt_llm.model == settings.LLM_MODEL

    search = get_default_search_provider()
    assert search is not None


