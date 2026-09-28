from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- LLM Contracts ---

class LLMMessage(BaseModel):
    role: str = Field(description="Role of the author: system, user, assistant")
    content: str = Field(description="Content of the message")


class LLMResponse(BaseModel):
    content: str = Field(description="Assistant response text")
    model: str = Field(description="Model used for generation")
    usage: Dict[str, Any] = Field(default_factory=dict, description="Token usage statistics")


class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat_complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate a chat completion from the provided messages."""
        pass

    @abstractmethod
    async def check_connectivity(self) -> bool:
        """Verify network connectivity and credentials with the model provider."""
        pass


# --- Embedding Contracts ---

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]] = Field(description="List of vector embeddings")
    model: str = Field(description="Embedding model used")
    dimensions: int = Field(description="Dimension size of each embedding vector")
    total_tokens: int = Field(default=0, description="Total tokens consumed")


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> EmbeddingResponse:
        """Generate vector embeddings for a batch of text strings."""
        pass

    @abstractmethod
    async def check_connectivity(self) -> bool:
        """Verify connectivity and credentials with the embedding provider."""
        pass


# --- Search Contracts ---

class SearchCitation(BaseModel):
    title: str = Field(description="Title of the source webpage or article")
    url: str = Field(description="Direct URL to the external reference")
    snippet: str = Field(description="Relevant text snippet or summary")
    source_name: Optional[str] = Field(default=None, description="Domain or publication name")
    published_at: Optional[str] = Field(default=None, description="Publication timestamp or date")


class SearchResult(BaseModel):
    query: str = Field(description="Original search query string")
    citations: List[SearchCitation] = Field(default_factory=list, description="List of external citations")
    raw_answer: Optional[str] = Field(default=None, description="Direct summary or answer if returned by search engine")


class BaseSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> SearchResult:
        """Execute a web search and return structured citations."""
        pass

    @abstractmethod
    async def check_connectivity(self) -> bool:
        """Verify connectivity with the search provider service."""
        pass
