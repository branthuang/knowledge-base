import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.knowledge import KnowledgeItem
from app.models.embedding import EmbeddingChunk
from app.providers.base import BaseEmbeddingProvider
from app.providers.openai_embedding import OpenAICompatibleEmbeddingProvider
from app.services.chunker import DocumentChunker, default_chunker

logger = logging.getLogger(__name__)


def get_default_embedding_provider() -> BaseEmbeddingProvider:
    """Instantiate default embedding provider from settings."""
    return OpenAICompatibleEmbeddingProvider(
        api_base=settings.EMBEDDING_API_BASE,
        api_key=settings.EMBEDDING_API_KEY,
        model=settings.EMBEDDING_MODEL_NAME,
        expected_dimensions=settings.EMBEDDING_DIMENSIONS,
    )


class IndexService:
    """
    Knowledge indexing service:
    1. Splits knowledge item content into structured chunks.
    2. Calls EmbeddingProvider in batches to generate vector representations.
    3. Persists chunks and embeddings to `embedding_chunks`.
    4. Updates `index_status` on KnowledgeItem.
    """

    def __init__(
        self,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        chunker: Optional[DocumentChunker] = None,
        batch_size: int = 16,
    ):
        self._provider = embedding_provider
        self.chunker = chunker or default_chunker
        self.batch_size = batch_size

    @property
    def provider(self) -> BaseEmbeddingProvider:
        if self._provider is None:
            self._provider = get_default_embedding_provider()
        return self._provider

    async def index_knowledge_item(
        self,
        session: AsyncSession,
        knowledge: KnowledgeItem,
    ) -> int:
        """
        Index a single KnowledgeItem:
        - Chunk blocks (or plain_text fallback).
        - Embed chunk texts.
        - Persist to embedding_chunks table.
        - Update index_status to 'indexed' (or 'failed' on error).
        Returns number of chunks indexed.
        """
        # 1. Chunk content
        chunks = []
        if knowledge.blocks_json and isinstance(knowledge.blocks_json, list) and len(knowledge.blocks_json) > 0:
            chunks = self.chunker.chunk_blocks(knowledge.blocks_json, title=knowledge.title)
        elif knowledge.plain_text and knowledge.plain_text.strip():
            chunks = self.chunker.chunk_plain_text(knowledge.plain_text, title=knowledge.title)

        # 2. If document is empty, clean up old chunks and set indexed
        if not chunks:
            await session.execute(
                delete(EmbeddingChunk).where(EmbeddingChunk.knowledge_id == knowledge.id)
            )
            knowledge.index_status = "indexed"
            await session.commit()
            return 0

        # 3. Generate embeddings in batches
        texts = [c.chunk_text for c in chunks]
        all_embeddings: List[List[float]] = []

        try:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                resp = await self.provider.embed_texts(batch)
                all_embeddings.extend(resp.embeddings)
        except Exception as e:
            logger.error("Failed to generate embeddings for knowledge %s: %s", knowledge.id, e)
            knowledge.index_status = "failed"
            await session.commit()
            raise e

        # 4. Clean up previous chunks for this knowledge item
        await session.execute(
            delete(EmbeddingChunk).where(EmbeddingChunk.knowledge_id == knowledge.id)
        )

        # 5. Insert new chunk records
        for chunk, emb in zip(chunks, all_embeddings):
            ec = EmbeddingChunk(
                knowledge_id=knowledge.id,
                block_id=chunk.block_id,
                chunk_text=chunk.chunk_text,
                embedding=emb,
                token_count=chunk.token_count,
            )
            session.add(ec)

        knowledge.index_status = "indexed"
        await session.commit()
        return len(chunks)

    async def remove_index(
        self,
        session: AsyncSession,
        knowledge_id: str,
    ) -> None:
        """Remove all embedding chunks for a knowledge item and set index_status to pending."""
        await session.execute(
            delete(EmbeddingChunk).where(EmbeddingChunk.knowledge_id == knowledge_id)
        )
        knowledge = await session.get(KnowledgeItem, knowledge_id)
        if knowledge:
            knowledge.index_status = "pending"
        await session.commit()

    async def reindex_all(
        self,
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Reindex all non-trashed knowledge items.
        Returns summary metrics.
        """
        stmt = (
            select(KnowledgeItem)
            .where(KnowledgeItem.status != "trashed")
            .order_by(KnowledgeItem.created_at.asc())
        )
        result = await session.execute(stmt)
        items = result.scalars().all()

        total = len(items)
        success = 0
        failed = 0
        total_chunks = 0

        for item in items:
            try:
                cnt = await self.index_knowledge_item(session, item)
                total_chunks += cnt
                success += 1
            except Exception as e:
                logger.error("Error reindexing item %s: %s", item.id, e)
                failed += 1

        return {
            "total_items": total,
            "successful_items": success,
            "failed_items": failed,
            "total_chunks": total_chunks,
        }


# Global default index service instance
default_index_service = IndexService()
