import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeItem
from app.models.category import Category
from app.models.tag import Tag, KnowledgeTag
from app.models.search_session import SearchSession
from app.schemas.workbench import (
    WorkbenchStatsResponse,
    WorkbenchActivitiesResponse,
    RecentKnowledgeItem,
    PendingReviewDraftItem,
    RecentSearchSessionItem,
    PopularTagItem,
)

logger = logging.getLogger(__name__)


class WorkbenchService:
    """
    Workbench Dashboard Domain Service:
    Aggregates macro knowledge base metrics, pending review drafts, recent activities, and search sessions.
    """

    async def get_workbench_stats(self, session: AsyncSession) -> WorkbenchStatsResponse:
        # 1. Total active knowledge
        stmt_total_k = select(func.count(KnowledgeItem.id)).where(KnowledgeItem.status != "trashed")
        res_total_k = await session.execute(stmt_total_k)
        total_knowledge = res_total_k.scalar() or 0

        # 2. Total active categories
        stmt_total_c = select(func.count(Category.id)).where(Category.status == "active")
        res_total_c = await session.execute(stmt_total_c)
        total_categories = res_total_c.scalar() or 0

        # 3. Total tags
        stmt_total_t = select(func.count(Tag.id))
        res_total_t = await session.execute(stmt_total_t)
        total_tags = res_total_t.scalar() or 0

        # 4. Monthly added count
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        stmt_month = select(func.count(KnowledgeItem.id)).where(
            KnowledgeItem.status != "trashed",
            KnowledgeItem.created_at >= month_start,
        )
        res_month = await session.execute(stmt_month)
        monthly_added_count = res_month.scalar() or 0

        # 5. AI Inflow count
        stmt_ai = select(func.count(KnowledgeItem.id)).where(
            KnowledgeItem.status != "trashed",
            KnowledgeItem.source_type == "ai_search",
        )
        res_ai = await session.execute(stmt_ai)
        ai_inflow_count = res_ai.scalar() or 0

        return WorkbenchStatsResponse(
            total_knowledge=total_knowledge,
            total_categories=total_categories,
            total_tags=total_tags,
            monthly_added_count=monthly_added_count,
            ai_inflow_count=ai_inflow_count,
        )

    async def get_workbench_activities(self, session: AsyncSession) -> WorkbenchActivitiesResponse:
        # 1. Recent knowledge items (top 5)
        stmt_recent_k = (
            select(KnowledgeItem)
            .options(selectinload(KnowledgeItem.category))
            .where(KnowledgeItem.status != "trashed")
            .order_by(desc(KnowledgeItem.updated_at))
            .limit(5)
        )
        res_recent_k = await session.execute(stmt_recent_k)
        recent_k_rows = res_recent_k.scalars().all()
        recent_knowledge = [
            RecentKnowledgeItem(
                id=item.id,
                title=item.title,
                summary=item.summary,
                category_id=item.category_id,
                category_name=item.category.name if item.category else None,
                status=item.status,
                updated_at=item.updated_at,
            )
            for item in recent_k_rows
        ]

        # 2. Pending review drafts (status == 'draft' and source_type == 'ai_search')
        stmt_pending = (
            select(KnowledgeItem)
            .options(selectinload(KnowledgeItem.category))
            .where(
                KnowledgeItem.status == "draft",
                KnowledgeItem.source_type == "ai_search",
            )
            .order_by(desc(KnowledgeItem.created_at))
        )
        res_pending = await session.execute(stmt_pending)
        all_pending = res_pending.scalars().all()
        pending_count = len(all_pending)
        pending_drafts = [
            PendingReviewDraftItem(
                id=item.id,
                title=item.title,
                summary=item.summary,
                category_name=item.category.name if item.category else None,
                source_type=item.source_type,
                created_at=item.created_at,
            )
            for item in all_pending[:5]
        ]

        # 3. Recent searches (top 5)
        stmt_searches = (
            select(SearchSession)
            .order_by(desc(SearchSession.created_at))
            .limit(5)
        )
        res_searches = await session.execute(stmt_searches)
        recent_searches = [
            RecentSearchSessionItem(
                id=s.id,
                query=s.query,
                mode=s.mode,
                saved_knowledge_id=s.saved_knowledge_id,
                created_at=s.created_at,
            )
            for s in res_searches.scalars().all()
        ]

        # 4. Popular tags (top 10 by association count)
        stmt_tags = (
            select(
                Tag.id,
                Tag.name,
                Tag.color,
                func.count(KnowledgeTag.id).label("cnt"),
            )
            .outerjoin(KnowledgeTag, KnowledgeTag.tag_id == Tag.id)
            .group_by(Tag.id, Tag.name, Tag.color)
            .order_by(desc(func.count(KnowledgeTag.id)), Tag.name.asc())
            .limit(10)
        )
        res_tags = await session.execute(stmt_tags)
        popular_tags = [
            PopularTagItem(
                id=row[0],
                name=row[1],
                color=row[2],
                knowledge_count=row[3] or 0,
            )
            for row in res_tags.all()
        ]

        return WorkbenchActivitiesResponse(
            recent_knowledge=recent_knowledge,
            pending_drafts=pending_drafts,
            pending_drafts_count=pending_count,
            recent_searches=recent_searches,
            popular_tags=popular_tags,
        )


default_workbench_service = WorkbenchService()
