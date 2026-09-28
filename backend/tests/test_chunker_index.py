import pytest
from typing import List
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.category import Category
from app.models.tag import Tag, KnowledgeTag
from app.models.knowledge import KnowledgeItem
from app.models.source import KnowledgeSource
from app.models.embedding import EmbeddingChunk
from app.core.config import settings
from app.providers.base import BaseEmbeddingProvider, EmbeddingResponse
from app.services.chunker import DocumentChunker, default_chunker
from app.services.index_service import IndexService
from app.schemas.block import BlockItem, BlockType, BlockProperties


# --- Mock Embedding Provider ---

class MockEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, dimensions: int = settings.EMBEDDING_DIMENSIONS):
        self.dimensions = dimensions
        self.calls = 0

    async def embed_texts(self, texts: List[str]) -> EmbeddingResponse:
        self.calls += 1
        embeddings = []
        for idx, text in enumerate(texts):
            # Create a simple deterministic mock vector based on text length
            vec = [float((len(text) + idx + i) % 100) / 100.0 for i in range(self.dimensions)]
            embeddings.append(vec)
        return EmbeddingResponse(
            embeddings=embeddings,
            model="mock-embed-v1",
            dimensions=self.dimensions,
            total_tokens=sum(len(t) for t in texts),
        )

    async def check_connectivity(self) -> bool:
        return True


# --- Fixtures ---

@pytest.fixture
async def test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Category.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(KnowledgeItem.__table__.create)
        await conn.run_sync(KnowledgeTag.__table__.create)
        await conn.run_sync(KnowledgeSource.__table__.create)
        await conn.run_sync(EmbeddingChunk.__table__.create)

    async with session_factory() as session:
        yield session

    await engine.dispose()


# --- Unit Tests: DocumentChunker ---

def test_chunker_basic_blocks():
    chunker = DocumentChunker(max_chunk_size=200, min_chunk_size=20, overlap_size=30)
    blocks = [
        BlockItem(id="b-h1", type=BlockType.HEADING, content="FastAPI 异步架构", properties=BlockProperties(level=1)),
        BlockItem(id="b-p1", type=BlockType.PARAGRAPH, content="FastAPI 基于 Starlette 与 Pydantic 构建。"),
        BlockItem(id="b-c1", type=BlockType.CODE, content="app = FastAPI()", properties=BlockProperties(language="python")),
    ]

    chunks = chunker.chunk_blocks(blocks)
    assert len(chunks) >= 1
    full_text = "\n\n".join(c.chunk_text for c in chunks)
    assert "FastAPI 异步架构" in full_text
    assert "Pydantic" in full_text
    assert "app = FastAPI()" in full_text
    assert chunks[0].block_id is not None
    assert chunks[0].token_count > 0


def test_chunker_large_block_subdivision():
    chunker = DocumentChunker(max_chunk_size=150, min_chunk_size=20, overlap_size=30)
    # Long text exceeding 150 chars
    long_content = "这是长文本测试段落。" * 20
    assert len(long_content) > 150

    blocks = [
        BlockItem(id="b-long", type=BlockType.PARAGRAPH, content=long_content)
    ]
    chunks = chunker.chunk_blocks(blocks)
    assert len(chunks) > 1
    # Check that chunks have overlap
    for c in chunks:
        assert len(c.chunk_text) <= 180  # within max window range
        assert c.block_id == "b-long"


def test_chunker_empty_and_plain_text():
    chunker = DocumentChunker()
    assert chunker.chunk_blocks([]) == []
    assert chunker.chunk_plain_text("") == []

    plain_chunks = chunker.chunk_plain_text("简单的纯文本内容。\n第二段内容。")
    assert len(plain_chunks) == 1
    assert "纯文本内容" in plain_chunks[0].chunk_text


# --- Unit Tests: IndexService ---

@pytest.mark.asyncio
async def test_index_knowledge_item_success(test_session):
    mock_provider = MockEmbeddingProvider()
    index_service = IndexService(embedding_provider=mock_provider)

    item = KnowledgeItem(
        title="Python 异步编程实践",
        summary="讲解 asyncio 与 event loop",
        blocks_json=[
            {"id": "b-1", "type": "heading", "content": "Asyncio 核心", "properties": {"level": 1}},
            {"id": "b-2", "type": "paragraph", "content": "事件循环是异步编程的核心调度器。"},
        ],
        plain_text="# Asyncio 核心\n\n事件循环是异步编程的核心调度器。",
        status="published",
    )
    test_session.add(item)
    await test_session.commit()

    # Index item
    count = await index_service.index_knowledge_item(test_session, item)
    assert count >= 1
    assert item.index_status == "indexed"
    assert mock_provider.calls >= 1

    # Verify chunks in database
    from sqlalchemy import select
    res = await test_session.execute(
        select(EmbeddingChunk).where(EmbeddingChunk.knowledge_id == item.id)
    )
    chunks = res.scalars().all()
    assert len(chunks) == count
    assert len(chunks[0].embedding) == settings.EMBEDDING_DIMENSIONS
    assert "Asyncio 核心" in chunks[0].chunk_text


@pytest.mark.asyncio
async def test_reindex_item_updates_chunks(test_session):
    mock_provider = MockEmbeddingProvider()
    index_service = IndexService(embedding_provider=mock_provider)

    item = KnowledgeItem(
        title="初始知识",
        plain_text="第一版文本内容",
        status="published",
    )
    test_session.add(item)
    await test_session.commit()

    # First index
    c1 = await index_service.index_knowledge_item(test_session, item)
    assert c1 == 1

    # Modify content and re-index
    item.plain_text = "第二版更新后的文本内容，包含了更多的细节。"
    c2 = await index_service.index_knowledge_item(test_session, item)
    assert c2 == 1

    from sqlalchemy import select
    res = await test_session.execute(
        select(EmbeddingChunk).where(EmbeddingChunk.knowledge_id == item.id)
    )
    chunks = res.scalars().all()
    assert len(chunks) == 1
    assert "第二版" in chunks[0].chunk_text


@pytest.mark.asyncio
async def test_index_item_failure_updates_status(test_session):
    mock_provider = MockEmbeddingProvider()
    mock_provider.embed_texts = AsyncMock(side_effect=RuntimeError("Embedding API connection error"))

    index_service = IndexService(embedding_provider=mock_provider)
    item = KnowledgeItem(
        title="失败测试",
        plain_text="内容文本",
        status="published",
    )
    test_session.add(item)
    await test_session.commit()

    with pytest.raises(RuntimeError):
        await index_service.index_knowledge_item(test_session, item)

    assert item.index_status == "failed"


@pytest.mark.asyncio
async def test_remove_index_and_reindex_all(test_session):
    mock_provider = MockEmbeddingProvider()
    index_service = IndexService(embedding_provider=mock_provider)

    item1 = KnowledgeItem(title="Item 1", plain_text="Content 1", status="published")
    item2 = KnowledgeItem(title="Item 2", plain_text="Content 2", status="published")
    item_trashed = KnowledgeItem(title="Item 3", plain_text="Content 3", status="trashed")
    test_session.add_all([item1, item2, item_trashed])
    await test_session.commit()

    summary = await index_service.reindex_all(test_session)
    assert summary["total_items"] == 2
    assert summary["successful_items"] == 2
    assert summary["failed_items"] == 0
    assert summary["total_chunks"] == 2

    # Remove index for item 1
    await index_service.remove_index(test_session, item1.id)
    assert item1.index_status == "pending"

    from sqlalchemy import select
    res = await test_session.execute(
        select(EmbeddingChunk).where(EmbeddingChunk.knowledge_id == item1.id)
    )
    assert len(res.scalars().all()) == 0
