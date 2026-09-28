import math
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeItem
from app.models.category import Category
from app.models.tag import Tag, KnowledgeTag
from app.models.source import KnowledgeSource
from app.schemas.knowledge import (
    KnowledgeCreate,
    KnowledgeUpdate,
    KnowledgeListItem,
    KnowledgeDetailResponse,
    PaginatedKnowledgeResponse,
    SourceInfoResponse,
)
from app.schemas.tag import TagResponse
from app.services.block_parser import extract_plain_text
from app.services.category_service import get_cascade_category_ids, get_category_by_id


async def create_knowledge(session: AsyncSession, data: KnowledgeCreate) -> KnowledgeItem:
    """Create a new knowledge item, derive plain text, bind tags and sources."""
    # 1. Validate category if specified
    if data.category_id:
        cat = await get_category_by_id(session, data.category_id)
        if not cat:
            raise ValueError(f"指定的分类不存在: {data.category_id}")

    # 2. Derive plain text from structured blocks
    derived_plain_text = extract_plain_text(data.blocks_json)

    # 3. Create knowledge item
    item = KnowledgeItem(
        title=data.title,
        summary=data.summary,
        blocks_json=data.blocks_json,
        plain_text=derived_plain_text,
        category_id=data.category_id,
        source_type=data.source_type,
        status=data.status,
        favorite=data.favorite,
        index_status="pending",
    )
    session.add(item)
    await session.flush()  # Flush to get item.id

    # 4. Bind tags
    if data.tag_ids:
        # Deduplicate tag IDs
        for tid in set(data.tag_ids):
            kt = KnowledgeTag(knowledge_id=item.id, tag_id=tid)
            session.add(kt)

    # 5. Bind sources
    if data.sources:
        for s in data.sources:
            src = KnowledgeSource(
                knowledge_id=item.id,
                type=s.type,
                url=s.url,
                title=s.title,
                metadata_json=s.metadata_json,
            )
            session.add(src)

    await session.commit()
    return await get_knowledge_by_id(session, item.id)


async def get_knowledge_by_id(session: AsyncSession, knowledge_id: str) -> Optional[KnowledgeItem]:
    """Retrieve single knowledge item with loaded category, tags and sources."""
    stmt = (
        select(KnowledgeItem)
        .options(
            selectinload(KnowledgeItem.category),
            selectinload(KnowledgeItem.tags),
            selectinload(KnowledgeItem.sources),
        )
        .where(KnowledgeItem.id == knowledge_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_knowledge(
    session: AsyncSession,
    knowledge_id: str,
    data: KnowledgeUpdate
) -> Optional[KnowledgeItem]:
    """Update knowledge item, re-derive plain text if blocks changed, update tags and sources."""
    item = await get_knowledge_by_id(session, knowledge_id)
    if not item:
        return None

    update_dict = data.model_dump(exclude_unset=True)

    # Update basic scalar fields
    for field in ("title", "summary", "category_id", "status", "favorite"):
        if field in update_dict:
            setattr(item, field, update_dict[field])

    # If blocks changed, re-derive plain text and mark index as pending
    if "blocks_json" in update_dict:
        item.blocks_json = update_dict["blocks_json"]
        item.plain_text = extract_plain_text(item.blocks_json)
        item.index_status = "pending"

    # If tags changed, replace all bindings
    if "tag_ids" in update_dict and update_dict["tag_ids"] is not None:
        await session.execute(delete(KnowledgeTag).where(KnowledgeTag.knowledge_id == knowledge_id))
        for tid in set(update_dict["tag_ids"]):
            session.add(KnowledgeTag(knowledge_id=knowledge_id, tag_id=tid))

    # If sources changed, replace all sources
    if "sources" in update_dict and update_dict["sources"] is not None:
        await session.execute(delete(KnowledgeSource).where(KnowledgeSource.knowledge_id == knowledge_id))
        for s in data.sources:
            session.add(
                KnowledgeSource(
                    knowledge_id=knowledge_id,
                    type=s.type,
                    url=s.url,
                    title=s.title,
                    metadata_json=s.metadata_json,
                )
            )

    await session.commit()
    return await get_knowledge_by_id(session, knowledge_id)


async def list_knowledge(
    session: AsyncSession,
    status: Optional[str] = None,
    category_id: Optional[str] = None,
    cascade_category: bool = True,
    tag_ids: Optional[List[str]] = None,
    source_type: Optional[str] = None,
    favorite: Optional[bool] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedKnowledgeResponse:
    """Query knowledge items with multi-dimensional filtering, cascade category support and pagination."""
    query = select(KnowledgeItem).options(
        selectinload(KnowledgeItem.category),
        selectinload(KnowledgeItem.tags),
    )

    # Status filter: default to excluding trashed unless explicitly asked
    if status:
        query = query.where(KnowledgeItem.status == status)
    else:
        query = query.where(KnowledgeItem.status != "trashed")

    # Category filter with cascade
    if category_id:
        if cascade_category:
            all_cat_ids = await get_cascade_category_ids(session, category_id)
            query = query.where(KnowledgeItem.category_id.in_(all_cat_ids))
        else:
            query = query.where(KnowledgeItem.category_id == category_id)

    # Tag filter
    if tag_ids:
        query = query.join(KnowledgeTag, KnowledgeTag.knowledge_id == KnowledgeItem.id)
        query = query.where(KnowledgeTag.tag_id.in_(tag_ids))
        query = query.group_by(KnowledgeItem.id)

    if source_type:
        query = query.where(KnowledgeItem.source_type == source_type)

    if favorite is not None:
        query = query.where(KnowledgeItem.favorite == favorite)

    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.where(
            or_(
                KnowledgeItem.title.ilike(like_pattern),
                KnowledgeItem.summary.ilike(like_pattern),
                KnowledgeItem.plain_text.ilike(like_pattern),
            )
        )

    # Count total items
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await session.execute(count_query)
    total = total_res.scalar() or 0

    # Paginate and sort
    query = query.order_by(KnowledgeItem.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    items_res = await session.execute(query)
    items = items_res.scalars().all()

    # Convert to DTO
    list_items: List[KnowledgeListItem] = []
    for item in items:
        list_items.append(
            KnowledgeListItem(
                id=item.id,
                title=item.title,
                summary=item.summary,
                category_id=item.category_id,
                category_name=item.category.name if item.category else None,
                tags=[TagResponse.model_validate(t) for t in item.tags],
                source_type=item.source_type,
                status=item.status,
                favorite=item.favorite,
                index_status=item.index_status,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )

    pages = math.ceil(total / page_size) if page_size > 0 else 1
    return PaginatedKnowledgeResponse(
        items=list_items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


async def move_to_trash(session: AsyncSession, knowledge_id: str) -> bool:
    """Soft delete: move knowledge item to trash and mark for search index removal."""
    item = await get_knowledge_by_id(session, knowledge_id)
    if not item:
        return False
    item.status = "trashed"
    item.index_status = "pending"
    await session.commit()
    return True


async def restore_from_trash(session: AsyncSession, knowledge_id: str) -> bool:
    """Restore knowledge item from trash to published."""
    item = await get_knowledge_by_id(session, knowledge_id)
    if not item or item.status != "trashed":
        return False
    item.status = "published"
    item.index_status = "pending"
    await session.commit()
    return True


async def permanent_delete(session: AsyncSession, knowledge_id: str) -> bool:
    """Physically and permanently delete a knowledge item."""
    item = await get_knowledge_by_id(session, knowledge_id)
    if not item:
        return False
    await session.delete(item)
    await session.commit()
    return True
