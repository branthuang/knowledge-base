from typing import List, Optional
from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tag import Tag, KnowledgeTag
from app.schemas.tag import TagCreate, TagUpdate, TagWithStatsResponse, TagResponse


async def list_tags(session: AsyncSession) -> List[TagResponse]:
    stmt = select(Tag).order_by(Tag.name.asc())
    result = await session.execute(stmt)
    return [TagResponse.model_validate(t) for t in result.scalars().all()]


async def list_tags_with_stats(session: AsyncSession) -> List[TagWithStatsResponse]:
    """Retrieve all tags with association count and latest usage time."""
    stmt = (
        select(
            Tag,
            func.count(KnowledgeTag.id).label("knowledge_count"),
            func.max(KnowledgeTag.created_at).label("last_used_at"),
        )
        .outerjoin(KnowledgeTag, KnowledgeTag.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(func.count(KnowledgeTag.id).desc(), Tag.name.asc())
    )
    result = await session.execute(stmt)
    rows = result.all()

    responses = []
    for tag, count, last_used in rows:
        responses.append(
            TagWithStatsResponse(
                id=tag.id,
                name=tag.name,
                parent_id=tag.parent_id,
                description=tag.description,
                color=tag.color,
                created_at=tag.created_at,
                updated_at=tag.updated_at,
                knowledge_count=count or 0,
                last_used_at=last_used,
            )
        )
    return responses


async def get_tag_by_id(session: AsyncSession, tag_id: str) -> Optional[Tag]:
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_tag_by_name(session: AsyncSession, name: str) -> Optional[Tag]:
    stmt = select(Tag).where(Tag.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_tag(session: AsyncSession, data: TagCreate) -> Tag:
    existing = await get_tag_by_name(session, data.name)
    if existing:
        raise ValueError(f"已存在同名标签: {data.name}")

    tag = Tag(
        name=data.name,
        parent_id=data.parent_id,
        description=data.description,
        color=data.color,
    )
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag


async def update_tag(session: AsyncSession, tag_id: str, data: TagUpdate) -> Optional[Tag]:
    tag = await get_tag_by_id(session, tag_id)
    if not tag:
        return None

    update_dict = data.model_dump(exclude_unset=True)
    if "name" in update_dict and update_dict["name"] != tag.name:
        existing = await get_tag_by_name(session, update_dict["name"])
        if existing and existing.id != tag_id:
            raise ValueError(f"标签名称已存在: {update_dict['name']}")

    for k, v in update_dict.items():
        setattr(tag, k, v)

    await session.commit()
    await session.refresh(tag)
    return tag


async def delete_tag(session: AsyncSession, tag_id: str) -> bool:
    tag = await get_tag_by_id(session, tag_id)
    if not tag:
        return False

    await session.execute(delete(KnowledgeTag).where(KnowledgeTag.tag_id == tag_id))
    await session.execute(delete(Tag).where(Tag.id == tag_id))
    await session.commit()
    return True


async def merge_tags(session: AsyncSession, source_tag_id: str, target_tag_id: str) -> TagResponse:
    """
    Safely merge source tag into target tag within a database transaction:
    1. Validate source and target tags exist and are different.
    2. Remove colliding links where knowledge is already bound to target.
    3. Update remaining links from source to target.
    4. Delete source tag cleanly.
    """
    if source_tag_id == target_tag_id:
        raise ValueError("源标签与目标标签不能相同")

    source_tag = await get_tag_by_id(session, source_tag_id)
    if not source_tag:
        raise ValueError(f"源标签不存在: {source_tag_id}")

    target_tag = await get_tag_by_id(session, target_tag_id)
    if not target_tag:
        raise ValueError(f"目标标签不存在: {target_tag_id}")

    # Fetch knowledge_ids already linked to target tag
    target_links_stmt = select(KnowledgeTag.knowledge_id).where(KnowledgeTag.tag_id == target_tag_id)
    target_links_res = await session.execute(target_links_stmt)
    target_k_ids = set(target_links_res.scalars().all())

    # 1. Delete source relations that would collide with existing target relations
    if target_k_ids:
        await session.execute(
            delete(KnowledgeTag).where(
                KnowledgeTag.tag_id == source_tag_id,
                KnowledgeTag.knowledge_id.in_(target_k_ids),
            )
        )

    # 2. Migrate remaining source relations to target
    await session.execute(
        update(KnowledgeTag)
        .where(KnowledgeTag.tag_id == source_tag_id)
        .values(tag_id=target_tag_id)
    )

    # 3. Delete source tag
    await session.execute(delete(Tag).where(Tag.id == source_tag_id))
    await session.commit()

    # Expire/refresh target tag
    session.expire_all()
    refreshed_target = await get_tag_by_id(session, target_tag_id)
    return TagResponse.model_validate(refreshed_target)
