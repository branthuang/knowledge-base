import logging
import re
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.search_session import SearchSession
from app.models.knowledge import KnowledgeItem
from app.models.category import Category
from app.models.tag import Tag
from app.schemas.block import BlockItem, BlockType, BlockProperties
from app.schemas.knowledge import KnowledgeCreate, KnowledgeUpdate, SourceInfoCreate
from app.schemas.search import SearchRequest
from app.schemas.inflow import (
    InflowPreviewRequest,
    InflowPreviewResponse,
    InflowConfirmRequest,
    InflowAction,
    InflowSourceItem,
    SimilarKnowledgeCandidate,
)
from app.services.block_parser import markdown_to_blocks
from app.services.category_service import list_categories
from app.services.tag_service import list_tags
from app.services.knowledge_service import (
    create_knowledge,
    update_knowledge,
    get_knowledge_by_id,
)
from app.services.search_service import HybridSearchService, default_search_service
from app.services.index_service import IndexService, default_index_service

logger = logging.getLogger(__name__)


class InflowService:
    """
    Knowledge Inflow Domain Service:
    1. Transforms AI search results / Markdown into structured BlockItem draft trees.
    2. Appends formatted citation reference blocks.
    3. Recommends metadata (title, summary, category, tags).
    4. Detects existing similar knowledge in the local base (duplicate warning if similarity >= 0.75).
    5. Confirms inflow persistence (create new or update existing), records sources, updates session link, and triggers indexing.
    """

    def __init__(
        self,
        search_svc: Optional[HybridSearchService] = None,
        index_svc: Optional[IndexService] = None,
    ):
        self.search_service = search_svc or default_search_service
        self.index_service = index_svc or default_index_service

    async def generate_preview(
        self,
        session: AsyncSession,
        request: InflowPreviewRequest,
    ) -> InflowPreviewResponse:
        query = ""
        raw_markdown = ""
        citations_data = []

        # 1. Retrieve content from session if session_id provided
        if request.session_id:
            sess = await session.get(SearchSession, request.session_id)
            if sess:
                query = sess.query or ""
                raw_markdown = sess.ai_answer or ""
                citations_data = sess.citations_json or []

        # Fallback to direct request parameters
        if not query and request.query:
            query = request.query
        if not raw_markdown and request.content_markdown:
            raw_markdown = request.content_markdown
        if not citations_data and request.citations:
            citations_data = request.citations

        # 2. Convert markdown into structured blocks
        blocks: List[BlockItem] = markdown_to_blocks(raw_markdown) if raw_markdown else []

        # 3. Format citations as reference blocks at the bottom
        sources_list: List[InflowSourceItem] = []
        if citations_data:
            blocks.append(BlockItem(type=BlockType.DIVIDER))
            blocks.append(
                BlockItem(
                    type=BlockType.HEADING,
                    content="参考资料与来源",
                    properties=BlockProperties(level=2),
                )
            )
            for c in citations_data:
                title = c.get("title") or "外部参考来源"
                url = c.get("url") or ""
                snippet = c.get("snippet") or ""
                domain = c.get("source_name") or ""

                link_content = f"[{title}]({url})" if url else title
                if domain:
                    link_content += f" - {domain}"

                blocks.append(
                    BlockItem(
                        type=BlockType.LIST,
                        content=link_content,
                        properties=BlockProperties(list_style="bullet"),
                    )
                )

                sources_list.append(
                    InflowSourceItem(
                        type="url" if url else "ai_search",
                        url=url,
                        title=title,
                        metadata_json={"snippet": snippet, "domain": domain},
                    )
                )

        # 4. Recommend Title
        recommended_title = query.strip()
        # If the first block is a Heading, prefer it
        for b in blocks:
            if b.type == BlockType.HEADING and isinstance(b.content, str) and b.content.strip():
                recommended_title = b.content.strip()
                break

        # 5. Recommend Summary
        recommended_summary = ""
        for b in blocks:
            if b.type == BlockType.PARAGRAPH and isinstance(b.content, str) and b.content.strip():
                p_text = b.content.strip()
                recommended_summary = p_text[:160] + ("..." if len(p_text) > 160 else "")
                break
        if not recommended_summary and raw_markdown:
            clean_md = " ".join(raw_markdown.split())
            recommended_summary = clean_md[:160] + ("..." if len(clean_md) > 160 else "")

        # 6. Intelligent Category & Tag Recommendation
        categories = await list_categories(session)
        tags = await list_tags(session)

        full_text = f"{recommended_title} {raw_markdown}".lower()

        rec_cat_id = None
        rec_cat_name = None
        for cat in categories:
            if cat.name.lower() in full_text:
                rec_cat_id = cat.id
                rec_cat_name = cat.name
                break

        rec_tag_ids = []
        rec_tag_names = []
        for tag in tags:
            if tag.name.lower() in full_text:
                rec_tag_ids.append(tag.id)
                rec_tag_names.append(tag.name)

        # 7. Similarity & Duplicate Detection (threshold 0.75)
        has_similar = False
        similar_candidates: List[SimilarKnowledgeCandidate] = []
        try:
            search_res = await self.search_service.search(
                session,
                SearchRequest(
                    query=recommended_title,
                    minimum_score=0.50,
                ),
            )
            for hit in search_res.items:
                if hit.score >= 0.65 or (hit.vector_score >= 0.70 and hit.score >= 0.55):
                    similar_candidates.append(
                        SimilarKnowledgeCandidate(
                            id=hit.id,
                            title=hit.title,
                            snippet=hit.best_snippet,
                            similarity_score=hit.score,
                            category_name=hit.category_name,
                            updated_at=hit.updated_at,
                        )
                    )
            has_similar = len(similar_candidates) > 0
        except Exception as e:
            logger.warning("Similarity duplicate check failed: %s", e)

        return InflowPreviewResponse(
            session_id=request.session_id,
            recommended_title=recommended_title,
            recommended_summary=recommended_summary,
            blocks=blocks,
            recommended_category_id=rec_cat_id,
            recommended_category_name=rec_cat_name,
            recommended_tag_ids=rec_tag_ids,
            recommended_tag_names=rec_tag_names,
            sources=sources_list,
            has_similar_knowledge=has_similar,
            similar_candidates=similar_candidates,
        )

    async def confirm_inflow(
        self,
        session: AsyncSession,
        request: InflowConfirmRequest,
    ) -> KnowledgeItem:
        """Persist confirmed inflow into knowledge_items, bind sources, update session, and index."""
        # Convert blocks to serializable dicts
        blocks_payload = [b.model_dump() for b in request.blocks]

        # Convert sources to SourceInfoCreate
        sources_payload = []
        if request.sources:
            for s in request.sources:
                sources_payload.append(
                    SourceInfoCreate(
                        type=s.type,
                        url=s.url,
                        title=s.title,
                        metadata_json=s.metadata_json,
                    )
                )

        target_item: Optional[KnowledgeItem] = None

        if request.action == InflowAction.UPDATE_EXISTING:
            if not request.target_knowledge_id:
                raise ValueError("更新已有知识时必须提供 target_knowledge_id")
            existing = await get_knowledge_by_id(session, request.target_knowledge_id)
            if not existing:
                raise ValueError(f"目标知识点不存在: {request.target_knowledge_id}")

            update_data = KnowledgeUpdate(
                title=request.title,
                summary=request.summary,
                blocks_json=blocks_payload,
                category_id=request.category_id,
                tag_ids=request.tag_ids,
                status=request.status,
                sources=sources_payload if sources_payload else None,
            )
            target_item = await update_knowledge(session, existing.id, update_data)
        else:
            # Create new knowledge item
            create_data = KnowledgeCreate(
                title=request.title,
                summary=request.summary,
                blocks_json=blocks_payload,
                category_id=request.category_id,
                tag_ids=request.tag_ids or [],
                source_type="ai_search",
                status=request.status,
                sources=sources_payload,
            )
            target_item = await create_knowledge(session, create_data)

        # Backfill search_session.saved_knowledge_id
        if request.session_id and target_item:
            sess = await session.get(SearchSession, request.session_id)
            if sess:
                sess.saved_knowledge_id = target_item.id
                await session.commit()

        # Trigger vector indexing
        if target_item:
            try:
                await self.index_service.index_knowledge_item(session, target_item)
            except Exception as e:
                logger.error("Failed to build vector index for in-flowed knowledge: %s", e)

        return target_item


# Global default inflow service instance
default_inflow_service = InflowService()
