import pytest
import httpx
from app.providers.base import LLMMessage, LLMResponse, EmbeddingResponse, SearchCitation, SearchResult
from app.providers.openai_provider import OpenAICompatibleProvider
from app.providers.openai_embedding import OpenAICompatibleEmbeddingProvider
from app.providers.search_provider import MockSearchProvider, get_search_provider


def test_provider_data_contracts():
    msg = LLMMessage(role="user", content="Hello AI")
    assert msg.role == "user"
    assert msg.content == "Hello AI"

    resp = LLMResponse(content="Hello human", model="gpt-4o", usage={"total_tokens": 15})
    assert resp.content == "Hello human"
    assert resp.usage["total_tokens"] == 15

    emb = EmbeddingResponse(embeddings=[[0.1, 0.2, 0.3]], model="text-embedding-3-small", dimensions=3)
    assert len(emb.embeddings[0]) == 3

    citation = SearchCitation(
        title="Doc 1",
        url="https://example.com/1",
        snippet="A snippet",
        source_name="Example",
    )
    assert citation.title == "Doc 1"

    search_res = SearchResult(query="test", citations=[citation], raw_answer="Answer")
    assert len(search_res.citations) == 1


@pytest.mark.asyncio
async def test_openai_llm_provider_with_mock_transport(monkeypatch):
    def mock_handler(request: httpx.Request):
        if request.url.path.endswith("/chat/completions"):
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "这是大模型模拟回答"}}],
                    "model": "gpt-4o-mini",
                    "usage": {"total_tokens": 42},
                },
            )
        elif request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "gpt-4o-mini"}]})
        return httpx.Response(404)

    mock_transport = httpx.MockTransport(mock_handler)
    provider = OpenAICompatibleProvider(
        api_base="https://mock.api.com/v1",
        api_key="test-key",
        model="gpt-4o-mini",
    )

    original_client_init = httpx.AsyncClient.__init__

    def patched_init(self, *args, **kwargs):
        kwargs["transport"] = mock_transport
        original_client_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    res = await provider.chat_complete([LLMMessage(role="user", content="Hi")])
    assert res.content == "这是大模型模拟回答"
    assert res.model == "gpt-4o-mini"
    assert res.usage["total_tokens"] == 42

    connected = await provider.check_connectivity()
    assert connected is True


@pytest.mark.asyncio
async def test_openai_embedding_provider_with_mock_transport(monkeypatch):
    def mock_handler(request: httpx.Request):
        if request.url.path.endswith("/embeddings"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"index": 0, "embedding": [0.123] * 1536}
                    ],
                    "model": "text-embedding-3-small",
                    "usage": {"total_tokens": 5},
                },
            )
        return httpx.Response(404)

    mock_transport = httpx.MockTransport(mock_handler)
    provider = OpenAICompatibleEmbeddingProvider(
        api_base="https://mock.api.com/v1",
        api_key="test-key",
        model="text-embedding-3-small",
        expected_dimensions=1536,
    )

    original_client_init = httpx.AsyncClient.__init__

    def patched_init(self, *args, **kwargs):
        kwargs["transport"] = mock_transport
        original_client_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    res = await provider.embed_texts(["hello world"])
    assert len(res.embeddings) == 1
    assert len(res.embeddings[0]) == 1536
    assert res.dimensions == 1536

    connected = await provider.check_connectivity()
    assert connected is True


@pytest.mark.asyncio
async def test_mock_search_provider():
    provider = get_search_provider()
    assert isinstance(provider, MockSearchProvider)

    res = await provider.search("Shopify CDN", max_results=2)
    assert res.query == "Shopify CDN"
    assert len(res.citations) == 2
    assert "Shopify CDN" in res.citations[0].title

    connected = await provider.check_connectivity()
    assert connected is True
