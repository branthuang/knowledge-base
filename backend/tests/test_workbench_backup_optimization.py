import pytest
import io
import json
import zipfile
import httpx
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.db.session import get_db_session
from app.models.category import Category
from app.models.tag import Tag, KnowledgeTag
from app.models.knowledge import KnowledgeItem
from app.models.source import KnowledgeSource
from app.models.embedding import EmbeddingChunk
from app.models.search_session import SearchSession
from app.schemas.block import BlockItem, BlockType
from app.schemas.optimization import OptimizationRequest, OptimizationMode
from app.providers.base import BaseLLMProvider, BaseEmbeddingProvider, LLMMessage, LLMResponse, EmbeddingResponse
from app.services.index_service import IndexService
from app.services.workbench_service import WorkbenchService
from app.services.optimization_service import OptimizationService
from app.services.backup_service import BackupService
from app.api import optimization as opt_api_module
from app.api import backup as backup_api_module


class MockOptimizationLLM(BaseLLMProvider):
    async def chat_complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> LLMResponse:
        polished_md = (
            "# 优化后的技术指南\n\n"
            "这是一段通顺流畅的段落描述。\n\n"
            "```python\n"
            "print('Hello Secure Code')\n"
            "```\n\n"
            "- 关键要点一\n"
            "- 关键要点二"
        )
        changes = "理顺了语句结构，保持代码块逐字不变，优化了列表展示。"
        response_text = f"<<<POLISHED>>>\n{polished_md}\n<<<CHANGES>>>\n{changes}"
        return LLMResponse(content=response_text, model="mock-optimizer", usage={})

    async def check_connectivity(self) -> bool:
        return True


class MockEmbedding(BaseEmbeddingProvider):
    async def embed_texts(self, texts: List[str]) -> EmbeddingResponse:
        dim = 1536
        return EmbeddingResponse(
            embeddings=[[0.05] * dim for _ in texts],
            model="mock-embed",
            dimensions=dim,
            total_tokens=sum(len(t) for t in texts),
        )

    async def check_connectivity(self) -> bool:
        return True


@pytest.fixture
async def m5_db():
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

    # Seed initial records
    async with session_factory() as session:
        cat = Category(id="cat-arch", name="架构设计", status="active")
        tag = Tag(id="tag-python", name="Python", color="#3776ab")
        session.add_all([cat, tag])

        # Published item
        k1 = KnowledgeItem(
            id="k-101",
            title="Python 微服务治理架构",
            summary="微服务服务发现与负载均衡",
            plain_text="微服务服务发现与负载均衡实践",
            category_id=cat.id,
            source_type="manual",
            status="published",
        )
        # AI inflow draft item (pending review)
        k2 = KnowledgeItem(
            id="k-102",
            title="AI 搜索临时草稿：FastAPI 性能指标",
            summary="性能分析与基准测试",
            plain_text="性能分析与基准测试",
            category_id=cat.id,
            source_type="ai_search",
            status="draft",
        )
        session.add_all([k1, k2])
        session.add(KnowledgeTag(knowledge_id=k1.id, tag_id=tag.id))

        # Source
        session.add(KnowledgeSource(knowledge_id=k1.id, type="url", url="https://example.com/arch", title="Arch Doc"))

        # Search session
        session.add(SearchSession(id="sess-101", query="微服务架构如何选型", mode="knowledge_first"))
        await session.commit()

    yield session_factory
    await engine.dispose()


# --- 1. Workbench Tests ---

@pytest.mark.asyncio
async def test_workbench_stats_and_activities(m5_db):
    wb_svc = WorkbenchService()
    async with m5_db() as session:
        stats = await wb_svc.get_workbench_stats(session)
        assert stats.total_knowledge == 2
        assert stats.total_categories == 1
        assert stats.total_tags == 1
        assert stats.ai_inflow_count == 1
        assert stats.monthly_added_count >= 1

        activities = await wb_svc.get_workbench_activities(session)
        assert len(activities.recent_knowledge) >= 1
        assert activities.pending_drafts_count == 1
        assert len(activities.pending_drafts) == 1
        assert activities.pending_drafts[0].id == "k-102"
        assert len(activities.recent_searches) == 1
        assert len(activities.popular_tags) == 1
        assert activities.popular_tags[0].knowledge_count == 1


@pytest.mark.asyncio
async def test_workbench_api_endpoints(m5_db):
    session_factory = m5_db
    async def _override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_db

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            res_stats = await client.get("/api/workbench/stats")
            assert res_stats.status_code == 200
            assert res_stats.json()["total_knowledge"] == 2

            res_act = await client.get("/api/workbench/activities")
            assert res_act.status_code == 200
            assert res_act.json()["pending_drafts_count"] == 1
    finally:
        app.dependency_overrides.clear()


# --- 2. AI Optimization Tests ---

@pytest.mark.asyncio
async def test_optimization_service_preserves_code(m5_db):
    mock_llm = MockOptimizationLLM()
    opt_svc = OptimizationService(llm_provider=mock_llm)

    async with m5_db() as session:
        req = OptimizationRequest(
            content_markdown="粗糙的文本描述。\n```python\nprint('Hello Secure Code')\n```",
            mode=OptimizationMode.CONCISE,
        )
        resp = await opt_svc.optimize_content(session, req)

        assert "优化后的技术指南" in resp.polished_text
        assert "print('Hello Secure Code')" in resp.polished_text
        assert len(resp.blocks) >= 3
        assert "理顺了语句结构" in resp.changes_summary


@pytest.mark.asyncio
async def test_optimization_api_endpoint(m5_db):
    session_factory = m5_db
    async def _override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_db
    mock_llm = MockOptimizationLLM()
    custom_opt_svc = OptimizationService(llm_provider=mock_llm)
    original_opt_svc = opt_api_module.default_optimization_service
    opt_api_module.default_optimization_service = custom_opt_svc

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/optimization/polish",
                json={"content_markdown": "测试待润色内容", "mode": "concise"},
            )
            assert res.status_code == 200
            data = res.json()
            assert "优化后" in data["polished_text"]
            assert len(data["blocks"]) >= 1
    finally:
        opt_api_module.default_optimization_service = original_opt_svc
        app.dependency_overrides.clear()


# --- 3. Backup & Restore Tests ---

@pytest.mark.asyncio
async def test_backup_export_and_restore_cycle(m5_db):
    mock_emb = MockEmbedding()
    index_svc = IndexService(embedding_provider=mock_emb)
    backup_svc = BackupService(index_svc=index_svc)

    zip_bytes = None
    async with m5_db() as session:
        # Export
        zip_bytes = await backup_svc.export_full_backup(session)
        assert len(zip_bytes) > 0

        # Inspect ZIP content
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            assert "manifest.json" in zf.namelist()
            assert "data.json" in zf.namelist()
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["stats"]["knowledge_count"] == 2
            assert manifest["checksum_sha256"] is not None

        # Export single markdown
        md_text = await backup_svc.export_single_markdown(session, "k-101")
        assert "# Python 微服务治理架构" in md_text
        assert "架构设计" in md_text
        assert "https://example.com/arch" in md_text

    # Restore into a fresh database
    engine_new = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory_new = async_sessionmaker(bind=engine_new, class_=AsyncSession, expire_on_commit=False)
    async with engine_new.begin() as conn:
        await conn.run_sync(Category.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(KnowledgeItem.__table__.create)
        await conn.run_sync(KnowledgeTag.__table__.create)
        await conn.run_sync(KnowledgeSource.__table__.create)
        await conn.run_sync(EmbeddingChunk.__table__.create)
        await conn.run_sync(SearchSession.__table__.create)

    async with session_factory_new() as session_new:
        restore_result = await backup_svc.restore_full_backup(session_new, zip_bytes)
        assert restore_result["status"] == "success"
        assert restore_result["restored_counts"]["knowledge_items"] == 2
        assert restore_result["restored_counts"]["categories"] == 1

        # Check restored item exists
        k = await session_new.get(KnowledgeItem, "k-101")
        assert k is not None
        assert k.title == "Python 微服务治理架构"

    await engine_new.dispose()


@pytest.mark.asyncio
async def test_backup_restore_tampered_fails(m5_db):
    backup_svc = BackupService()
    # Create a corrupted zip with tampered data
    manifest_bytes = json.dumps({"checksum_sha256": "wrong-hash"}).encode("utf-8")
    data_bytes = json.dumps({"categories": []}).encode("utf-8")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("manifest.json", manifest_bytes)
        zf.writestr("data.json", data_bytes)
    corrupted_zip = buf.getvalue()

    async with m5_db() as session:
        with pytest.raises(ValueError) as exc_info:
            await backup_svc.restore_full_backup(session, corrupted_zip)
        assert "校验和不匹配" in str(exc_info.value)


@pytest.mark.asyncio
async def test_backup_api_endpoints(m5_db):
    session_factory = m5_db
    async def _override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_db

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. GET /api/backup/export
            export_res = await client.get("/api/backup/export")
            assert export_res.status_code == 200
            assert export_res.headers["content-type"] == "application/zip"
            zip_content = export_res.content

            # 2. GET /api/backup/export/markdown/{id}
            md_res = await client.get("/api/backup/export/markdown/k-101")
            assert md_res.status_code == 200
            assert "Python 微服务治理架构" in md_res.text

            # 3. POST /api/backup/restore
            restore_res = await client.post(
                "/api/backup/restore",
                content=zip_content,
                headers={"Content-Type": "application/zip"},
            )
            assert restore_res.status_code == 200
            assert restore_res.json()["status"] == "success"
    finally:
        app.dependency_overrides.clear()
