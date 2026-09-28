import pytest
from app.models.category import Category
from app.models.tag import Tag, KnowledgeTag
from app.models.knowledge import KnowledgeItem
from app.models.source import KnowledgeSource
from app.models.search_session import SearchSession
from app.models.embedding import EmbeddingChunk
from app.models.asset import Asset


def test_category_instantiation():
    cat = Category(name="技术类", description="技术相关知识", icon="code", sort_order=1)
    assert cat.name == "技术类"
    assert cat.status == "active"
    assert cat.sort_order == 1
    assert cat.id is not None


def test_category_hierarchy():
    parent = Category(id="cat-parent-1", name="技术类")
    child = Category(id="cat-child-1", name="Shopify", parent_id=parent.id)
    assert child.parent_id == "cat-parent-1"


def test_tag_instantiation():
    tag = Tag(name="Shopify", color="#008060")
    assert tag.name == "Shopify"
    assert tag.color == "#008060"
    assert tag.id is not None


def test_knowledge_item_defaults():
    item = KnowledgeItem(
        title="测试知识点",
        blocks_json=[{"id": "b1", "type": "paragraph", "content": "Hello"}],
        plain_text="Hello",
    )
    assert item.title == "测试知识点"
    assert item.status == "draft"
    assert item.source_type == "manual"
    assert item.index_status == "pending"
    assert item.favorite is False
    assert len(item.blocks_json) == 1


def test_knowledge_source():
    source = KnowledgeSource(
        knowledge_id="k-1",
        type="ai_search",
        url="https://example.com/doc",
        title="Example Source",
        metadata_json={"query": "how to config"},
    )
    assert source.knowledge_id == "k-1"
    assert source.type == "ai_search"
    assert source.url == "https://example.com/doc"


def test_search_session():
    session = SearchSession(
        query="Shopify CDN 配置",
        mode="knowledge_first",
        local_hits_json=[{"id": "k-1", "score": 0.82}],
        ai_answer="可以通过 Cloudflare CDN 接入...",
        citations_json=[{"title": "Shopify Docs", "url": "https://help.shopify.com"}],
        provider="openai",
        model="gpt-4o-mini",
    )
    assert session.query == "Shopify CDN 配置"
    assert session.mode == "knowledge_first"
    assert len(session.local_hits_json) == 1
    assert session.saved_knowledge_id is None


def test_embedding_chunk():
    chunk = EmbeddingChunk(
        knowledge_id="k-1",
        block_id="b-1",
        chunk_text="一段用于语义检索的正文分块",
        token_count=16,
    )
    assert chunk.knowledge_id == "k-1"
    assert chunk.block_id == "b-1"
    assert chunk.token_count == 16


def test_asset_model():
    asset = Asset(
        storage_key="uploads/2026/09/image.png",
        mime_type="image/png",
        size=10240,
        hash="sha256hashvalue",
        metadata_json={"width": 800, "height": 600},
    )
    assert asset.storage_key == "uploads/2026/09/image.png"
    assert asset.size == 10240
