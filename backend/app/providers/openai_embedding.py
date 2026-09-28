import logging
from typing import List
import httpx
from app.providers.base import BaseEmbeddingProvider, EmbeddingResponse

logger = logging.getLogger(__name__)


class OpenAICompatibleEmbeddingProvider(BaseEmbeddingProvider):
    """Universal OpenAI-compatible text embeddings adapter."""

    def __init__(self, api_base: str, api_key: str, model: str, expected_dimensions: int = 1536, timeout: float = 30.0):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.expected_dimensions = expected_dimensions
        self.timeout = timeout

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def embed_texts(self, texts: List[str]) -> EmbeddingResponse:
        if not self.api_key or self.api_key in ("mock-key", "your-api-key-here"):
            vectors = []
            for idx, text in enumerate(texts):
                vec = [float((len(text) + idx + i) % 100) / 100.0 for i in range(self.expected_dimensions)]
                vectors.append(vec)
            return EmbeddingResponse(
                embeddings=vectors,
                model="local-mock-embeddings",
                dimensions=self.expected_dimensions,
                total_tokens=sum(len(t) for t in texts),
            )

        url = f"{self.api_base}/embeddings"
        payload = {
            "model": self.model,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=self._headers())
            response.raise_for_status()
            data = response.json()

        embeddings_data = data["data"]
        # Sort by index to maintain ordering
        embeddings_data.sort(key=lambda x: x["index"])
        vectors = [item["embedding"] for item in embeddings_data]

        actual_dim = len(vectors[0]) if vectors else self.expected_dimensions
        total_tokens = data.get("usage", {}).get("total_tokens", 0)

        return EmbeddingResponse(
            embeddings=vectors,
            model=data.get("model", self.model),
            dimensions=actual_dim,
            total_tokens=total_tokens,
        )

    async def check_connectivity(self) -> bool:
        """Check embedding provider connectivity with a probe token."""
        try:
            resp = await self.embed_texts(["ping"])
            return len(resp.embeddings) == 1
        except Exception as e:
            logger.warning("Embedding provider connectivity check failed: %s", e)
            return False
