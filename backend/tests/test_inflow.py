import pytest
from typing import List
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.category import Category
from app.models.tag import Tag, KnowledgeTag
from app.models.knowledge import KnowledgeItem
from app.models.source import KnowledgeSource
from app.models.embedding import EmbeddingChunk
from app.models.search_session import SearchSession
from app.schemas.block import BlockItem, BlockType
from app.schemas.inflow import (
    InflowPreviewRequest,
    InflowConfirmRequest,
    InflowAction,
    InflowSourceItem,
)
from app.providers.base import BaseEmbeddingProvider, EmbeddingResponse
from app.services.index_service import IndexService
from app.services.search_service import HybridSearchService
from app.services.inflow_service import InflowService


class MockEmbedding(BaseEmbeddingProvider):
    async def embed_texts(self, texts: List[str]) -> EmbeddingResponse:
        dim = 1536
        embeddings = []
        for t in texts:
            vec = [0.1] * dim
            if "docker" in t.lower() or "容器" in t:
                vec[0] = 0.95
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
async def inflow_db():
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

    # Seed Category and Tag
    async with session_factory() as session:
        cat_devops = Category(name="运维与云原生", description="DevOps")
        tag_docker = Tag(name="Docker", color="#2496ed")
        session.add_all([cat_devops, tag_docker])

        # Pre-existing knowledge item for similarity test
        existing_k = KnowledgeItem(
            id="k-existing-docker",
            title="Docker 容器化部署实战",
            summary="Docker 基础命令与 Dockerfile 构建最佳实践",
            plain_text="Docker 基础命令与 Dockerfile 构建最佳实践",
            status="published",
        )
        session.add(existing_k)

        # Seed SearchSession
        sess = SearchSession(
            id="sess-docker-1",
            query="Docker 容器化部署实战指南",
            mode="knowledge_first",
            ai_answer="## Docker 容器化最佳实践\n\nDocker 容器化显著简化了应用的交付与隔离。\n\n```dockerfile\nFROM python:3.9-slim\nWORKDIR /app\n```",
            citations_json=[
                {
                    "title": "Docker 官方文档",
                    "url": "https://docs.docker.com",
                    "snippet": "Containerization guide",
                    "source_name": "docs.docker.com",
                }
            ],
        )
        session.add(sess)
        await session.commit()

        # Index existing_k
        idx_svc = IndexService(embedding_provider=MockEmbedding())
        await idx_svc.index_knowledge_item(session, existing_k)

    yield session_factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_generate_inflow_preview_with_session_and_similarity(inflow_db):
    mock_emb = MockEmbedding()
    search_svc = HybridSearchService(embedding_provider=mock_emb)
    index_svc = IndexService(embedding_provider=mock_emb)
    inflow_svc = InflowService(search_svc=search_svc, index_svc=index_svc)

    async with inflow_db() as session:
        req = InflowPreviewRequest(session_id="sess-docker-1")
        preview = await inflow_svc.generate_preview(session, req)

        assert preview.session_id == "sess-docker-1"
        assert preview.recommended_title == "Docker 容器化最佳实践"
        assert "简化了应用的交付" in preview.recommended_summary
        assert len(preview.blocks) >= 3  # Heading, Paragraph, Code, Divider, Heading, List
        assert len(preview.sources) == 1
        assert preview.sources[0].url == "https://docs.docker.com"

        # Check intelligent recommendation
        assert preview.recommended_tag_names == ["Docker"]

        # Check duplicate similarity detection (hits k-existing-docker)
        assert preview.has_similar_knowledge is True
        assert len(preview.similar_candidates) >= 1
        assert preview.similar_candidates[0].id == "k-existing-docker"
        assert preview.similar_candidates[0].similarity_score >= 0.60


@pytest.mark.asyncio
async def test_confirm_inflow_create_new(inflow_db):
    mock_emb = MockEmbedding()
    search_svc = HybridSearchService(embedding_provider=mock_emb)
    index_svc = IndexService(embedding_provider=mock_emb)
    inflow_svc = InflowService(search_svc=search_svc, index_svc=index_svc)

    async with inflow_db() as session:
        confirm_req = InflowConfirmRequest(
            session_id="sess-docker-1",
            action=InflowAction.CREATE_NEW,
            title="Docker 生产环境多阶段构建",
            summary="解析多阶段构建如何有效缩减镜像体积",
            blocks=[
                BlockItem(type=BlockType.HEADING, content="多阶段构建"),
                BlockItem(type=BlockType.PARAGRAPH, content="通过多阶段构建过滤编译期依赖。"),
            ],
            sources=[
                InflowSourceItem(
                    type="url",
                    url="https://docs.docker.com/build",
                    title="Docker Build Guide",
                )
            ],
            status="published",
        )

        item = await inflow_svc.confirm_inflow(session, confirm_req)
        assert item is not None
        assert item.id != "k-existing-docker"
        assert item.source_type == "ai_search"
        assert item.title == "Docker 生产环境多阶段构建"
        assert item.index_status == "indexed"
        assert len(item.sources) == 1
        assert item.sources[0].url == "https://docs.docker.com/build"

        # Verify session saved_knowledge_id is backfilled
        sess = await session.get(SearchSession, "sess-docker-1")
        assert sess.saved_knowledge_id == item.id


@pytest.mark.asyncio
async def test_confirm_inflow_update_existing(inflow_db):
    mock_emb = MockEmbedding()
    search_svc = HybridSearchService(embedding_provider=mock_emb)
    index_svc = IndexService(embedding_provider=mock_emb)
    inflow_svc = InflowService(search_svc=search_svc, index_svc=index_svc)

    async with inflow_db() as session:
        confirm_req = InflowConfirmRequest(
            session_id="sess-docker-1",
            action=InflowAction.UPDATE_EXISTING,
            target_knowledge_id="k-existing-docker",
            title="Docker 容器化部署实战（已合并 AI 搜索结果）",
            summary="合并了最新最佳实践的新版本",
            blocks=[
                BlockItem(type=BlockType.PARAGRAPH, content="合并后的正文内容。"),
            ],
            status="published",
        )

        updated_item = await inflow_svc.confirm_inflow(session, confirm_req)
        assert updated_item.id == "k-existing-docker"
        assert updated_item.title == "Docker 容器化部署实战（已合并 AI 搜索结果）"

        # Check session link
        sess = await session.get(SearchSession, "sess-docker-1")
        assert sess.saved_knowledge_id == "k-existing-docker"
