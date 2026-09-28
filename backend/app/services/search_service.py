import re
import math
import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeItem
from app.models.category import Category
from app.models.tag import Tag, KnowledgeTag
from app.models.embedding import EmbeddingChunk
from app.schemas.tag import TagResponse
from app.schemas.search import SearchRequest, SearchResponse, SearchHitItem
from app.services.category_service import get_cascade_category_ids
from app.services.index_service import get_default_embedding_provider
from app.providers.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


def cosine_similarity(v1: Optional[List[float]], v2: Optional[List[float]]) -> float:
    """Compute cosine similarity between two float vectors in [0.0, 1.0]."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0
    for a, b in zip(v1, v2):
        dot += a * b
        norm1 += a * a
        norm2 += b * b
    if norm1 <= 0.0 or norm2 <= 0.0:
        return 0.0
    sim = dot / (math.sqrt(norm1) * math.sqrt(norm2))
    return max(0.0, min(1.0, float(sim)))


def extract_snippet(text: str, query: str, terms: List[str], max_len: int = 160) -> str:
    """Extract contextual snippet around matching keywords."""
    if not text:
        return ""
    text_clean = " ".join(text.split())
    if len(text_clean) <= max_len:
        return text_clean

    lower_text = text_clean.lower()
    target_idx = -1
    idx = lower_text.find(query.lower())
    if idx != -1:
        target_idx = idx
    else:
        for t in terms:
            idx = lower_text.find(t.lower())
            if idx != -1:
                target_idx = idx
                break

    if target_idx == -1:
        return text_clean[:max_len] + "..."

    start = max(0, target_idx - 30)
    end = min(len(text_clean), start + max_len)
    snippet = text_clean[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text_clean):
        snippet = snippet + "..."
    return snippet


class HybridSearchService:
    """
    Hybrid Search Engine implementing:
    1. Multi-way recall: Keyword FTS weighted scoring + Vector cosine similarity.
    2. Multi-dimensional structured filtering: cascade categories, multi-tags, date range, favorite, status.
    3. Normalization & Weighted Fusion:
       FusedScore = 0.4 * KeywordScore + 0.5 * VectorScore + 0.1 * TitleBonus
    4. Aggregation by KnowledgeItem & Best Snippet extraction.
    5. Local Knowledge Sufficiency Evaluation (is_sufficient, AI search guidance).
    """

    def __init__(self, embedding_provider: Optional[BaseEmbeddingProvider] = None):
        self._provider = embedding_provider

    @property
    def provider(self) -> BaseEmbeddingProvider:
        if self._provider is None:
            self._provider = get_default_embedding_provider()
        return self._provider

    async def search(self, session: AsyncSession, request: SearchRequest) -> SearchResponse:
        q_raw = request.query.strip()
        terms = [t for t in re.split(r"[\s,，、；;]+", q_raw) if t]

        # 1. Resolve structured filters
        conditions = [KnowledgeItem.status != "trashed"]

        # Category cascade filter
        if request.category_id:
            cascade_cat_ids = await get_cascade_category_ids(session, request.category_id)
            if cascade_cat_ids:
                conditions.append(KnowledgeItem.category_id.in_(cascade_cat_ids))
            else:
                conditions.append(KnowledgeItem.category_id == request.category_id)

        # Tag filter
        if request.tag_ids:
            tag_subq = (
                select(KnowledgeTag.knowledge_id)
                .where(KnowledgeTag.tag_id.in_(request.tag_ids))
            )
            conditions.append(KnowledgeItem.id.in_(tag_subq))

        # Source type filter
        if request.source_type:
            conditions.append(KnowledgeItem.source_type == request.source_type)

        # Favorite filter
        if request.favorite is not None:
            conditions.append(KnowledgeItem.favorite == request.favorite)

        # Date range filters
        if request.start_date:
            conditions.append(KnowledgeItem.updated_at >= request.start_date)
        if request.end_date:
            conditions.append(KnowledgeItem.updated_at <= request.end_date)

        # 2. Retrieve filtered candidate knowledge items
        stmt = (
            select(KnowledgeItem)
            .options(
                selectinload(KnowledgeItem.category),
                selectinload(KnowledgeItem.tags),
                selectinload(KnowledgeItem.chunks),
            )
            .where(*conditions)
        )
        res = await session.execute(stmt)
        candidates = res.scalars().all()

        if not candidates:
            return SearchResponse(
                query=q_raw,
                total=0,
                page=request.page,
                page_size=request.page_size,
                is_sufficient=False,
                ai_search_suggested=True,
                ai_search_prompt="本地知识库中未找到足够匹配的内容，建议使用 AI 搜索获取更全面的解答",
                items=[],
            )

        # 3. Vector embedding generation for query
        query_vec: Optional[List[float]] = None
        try:
            emb_res = await self.provider.embed_texts([q_raw])
            if emb_res.embeddings:
                query_vec = emb_res.embeddings[0]
        except Exception as e:
            logger.warning("Embedding query generation failed, proceeding with keyword recall: %s", e)

        # 4. Multi-way scoring & Aggregation per KnowledgeItem
        q_lower = q_raw.lower()
        scored_items: List[SearchHitItem] = []

        for item in candidates:
            # --- Vector Recall & Similarity ---
            best_vec_sim = 0.0
            best_chunk: Optional[EmbeddingChunk] = None

            if query_vec and item.chunks:
                for chunk in item.chunks:
                    chunk_emb = chunk.embedding
                    # Convert pgvector Vector object to list if needed
                    if hasattr(chunk_emb, "tolist"):
                        chunk_emb = chunk_emb.tolist()
                    elif chunk_emb and not isinstance(chunk_emb, list):
                        chunk_emb = list(chunk_emb)

                    sim = cosine_similarity(query_vec, chunk_emb)
                    if sim > best_vec_sim:
                        best_vec_sim = sim
                        best_chunk = chunk

            # --- Keyword Recall & Weighted Matching ---
            raw_kw_score = 0.0
            item_title_lower = item.title.strip().lower()
            item_summary_lower = (item.summary or "").lower()
            item_plain_lower = (item.plain_text or "").lower()

            # Exact title match
            if q_lower == item_title_lower:
                raw_kw_score += 15.0
            elif q_lower in item_title_lower:
                raw_kw_score += 10.0

            # Term level matching
            if terms:
                title_hits = sum(1 for t in terms if t.lower() in item_title_lower)
                raw_kw_score += 6.0 * (title_hits / len(terms))

                tag_names = " ".join(t.name.lower() for t in item.tags)
                tag_hits = sum(1 for t in terms if t.lower() in tag_names)
                raw_kw_score += 5.0 * (tag_hits / len(terms))

                if item_summary_lower:
                    sum_hits = sum(1 for t in terms if t.lower() in item_summary_lower)
                    raw_kw_score += 4.0 * (sum_hits / len(terms))

                if item_plain_lower:
                    content_hits = sum(item_plain_lower.count(t.lower()) for t in terms)
                    raw_kw_score += min(6.0, content_hits * 1.5)

            kw_score_norm = min(1.0, raw_kw_score / 20.0)

            # Title Bonus (10% bonus if query substring or exact in title)
            title_bonus = 1.0 if (q_lower in item_title_lower) else 0.0

            # Weighted Fused Score: 40% Keyword + 50% Vector + 10% Title Bonus
            fused_score = (0.4 * kw_score_norm) + (0.5 * best_vec_sim) + (0.1 * title_bonus)
            fused_score = round(max(0.0, min(1.0, fused_score)), 4)

            # Filter out completely unrelated candidates (zero keyword hits and negligible vector similarity)
            if fused_score <= 0.05 and kw_score_norm == 0.0:
                continue

            # --- Best Snippet & Block Extraction ---
            snippet_source = ""
            matched_block_id = None
            if best_chunk and best_vec_sim >= 0.3:
                snippet_source = best_chunk.chunk_text
                matched_block_id = best_chunk.block_id
            else:
                # Find chunk with most keyword matches
                best_kw_chunk = None
                best_kw_count = 0
                for c in item.chunks:
                    c_lower = c.chunk_text.lower()
                    cnt = sum(c_lower.count(t.lower()) for t in terms)
                    if cnt > best_kw_count:
                        best_kw_count = cnt
                        best_kw_chunk = c
                if best_kw_chunk:
                    snippet_source = best_kw_chunk.chunk_text
                    matched_block_id = best_kw_chunk.block_id
                elif item.summary:
                    snippet_source = item.summary
                else:
                    snippet_source = item.plain_text

            best_snippet = extract_snippet(snippet_source, q_raw, terms)

            tag_responses = [TagResponse.model_validate(t) for t in item.tags]

            hit = SearchHitItem(
                id=item.id,
                title=item.title,
                summary=item.summary,
                category_id=item.category_id,
                category_name=item.category.name if item.category else None,
                tags=tag_responses,
                source_type=item.source_type,
                favorite=item.favorite,
                score=fused_score,
                keyword_score=round(kw_score_norm, 4),
                vector_score=round(best_vec_sim, 4),
                best_snippet=best_snippet,
                matched_block_id=matched_block_id,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            scored_items.append(hit)

        # 5. Sort by fused score descending
        scored_items.sort(key=lambda x: x.score, reverse=True)

        total_hits = len(scored_items)

        # 6. Sufficiency Evaluation
        top_1_score = scored_items[0].score if scored_items else 0.0
        is_sufficient = (total_hits > 0) and (top_1_score >= request.minimum_score)
        ai_search_suggested = not is_sufficient
        ai_search_prompt = (
            "本地知识库中未找到足够匹配的内容，建议使用 AI 搜索获取更全面的解答"
            if ai_search_suggested
            else None
        )

        # 7. Pagination
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        paged_items = scored_items[start_idx:end_idx]

        return SearchResponse(
            query=q_raw,
            total=total_hits,
            page=request.page,
            page_size=request.page_size,
            is_sufficient=is_sufficient,
            ai_search_suggested=ai_search_suggested,
            ai_search_prompt=ai_search_prompt,
            items=paged_items,
        )


# Global default search service instance
default_search_service = HybridSearchService()
