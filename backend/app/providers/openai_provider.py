import logging
from typing import List, Optional, Any
import httpx
from app.providers.base import BaseLLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseLLMProvider):
    """Universal OpenAI-compatible API client adapter."""

    def __init__(self, api_base: str, api_key: str, model: str, timeout: float = 30.0):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def chat_complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> LLMResponse:
        url = f"{self.api_base}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [msg.model_dump() for msg in messages],
            "temperature": temperature,
            **kwargs,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=self._headers())
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage", {})
        model_used = data.get("model", self.model)

        return LLMResponse(content=content, model=model_used, usage=usage)

    async def check_connectivity(self) -> bool:
        """Check provider connectivity by testing /models endpoint or simple completion."""
        url = f"{self.api_base}/models"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=self._headers())
                return resp.status_code == 200
        except Exception as e:
            logger.warning("OpenAI provider connectivity check failed: %s", e)
            return False
