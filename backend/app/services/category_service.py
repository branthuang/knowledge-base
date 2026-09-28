from typing import List, Optional, Dict
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.models.knowledge import KnowledgeItem
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryTreeNode, CategoryResponse


async def list_categories(session: AsyncSession, status: Optional[str] = None) -> List[CategoryResponse]:
    """List all categories with knowledge count."""
    stmt = (
        select(
            Category,
            func.count(KnowledgeItem.id).label("knowledge_count")
        )
        .outerjoin(KnowledgeItem, KnowledgeItem.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.sort_order.asc(), Category.created_at.asc())
    )
    if status:
        stmt = stmt.where(Category.status == status)

    result = await session.execute(stmt)
    rows = result.all()

    responses = []
    for cat, count in rows:
        resp = CategoryResponse(
            id=cat.id,
            name=cat.name,
            parent_id=cat.parent_id,
            description=cat.description,
            icon=cat.icon,
            color=cat.color,
            sort_order=cat.sort_order,
            status=cat.status,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
            knowledge_count=count,
        )
        responses.append(resp)
    return responses


async def get_category_tree(session: AsyncSession, status: Optional[str] = None) -> List[CategoryTreeNode]:
    """Retrieve hierarchical category tree structure."""
    all_cats = await list_categories(session, status=status)
    cat_map: Dict[str, CategoryTreeNode] = {}
    root_nodes: List[CategoryTreeNode] = []

    for cat in all_cats:
        node = CategoryTreeNode(
            id=cat.id,
            name=cat.name,
            parent_id=cat.parent_id,
            description=cat.description,
            icon=cat.icon,
            color=cat.color,
            sort_order=cat.sort_order,
            status=cat.status,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
            knowledge_count=cat.knowledge_count,
            children=[],
        )
        cat_map[node.id] = node

    for node in cat_map.values():
        if node.parent_id and node.parent_id in cat_map:
            cat_map[node.parent_id].children.append(node)
        else:
            root_nodes.append(node)

    return root_nodes


async def get_cascade_category_ids(session: AsyncSession, parent_cat_id: str) -> List[str]:
    """
    Recursively retrieve parent category id and all of its descendant subcategory ids.
    Enables cascade filtering: selecting parent includes all subcategories.
    """
    stmt = select(Category.id, Category.parent_id)
    result = await session.execute(stmt)
    rows = result.all()

    # Build adjacency list: parent -> list of children
    children_map: Dict[str, List[str]] = {}
    for cid, pid in rows:
        if pid:
            children_map.setdefault(pid, []).append(cid)

    collected_ids: List[str] = []

    def _collect(cid: str):
        collected_ids.append(cid)
        for child_id in children_map.get(cid, []):
            _collect(child_id)

    _collect(parent_cat_id)
    return collected_ids


async def get_category_by_id(session: AsyncSession, cat_id: str) -> Optional[Category]:
    stmt = select(Category).where(Category.id == cat_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_category(session: AsyncSession, data: CategoryCreate) -> Category:
    cat = Category(
        name=data.name,
        parent_id=data.parent_id,
        description=data.description,
        icon=data.icon,
        color=data.color,
        sort_order=data.sort_order,
        status=data.status,
    )
    session.add(cat)
    await session.commit()
    await session.refresh(cat)
    return cat


async def update_category(session: AsyncSession, cat_id: str, data: CategoryUpdate) -> Optional[Category]:
    cat = await get_category_by_id(session, cat_id)
    if not cat:
        return None

    update_dict = data.model_dump(exclude_unset=True)
    # Prevent category from becoming its own parent
    if update_dict.get("parent_id") == cat_id:
        raise ValueError("分类不能设置自身为父分类")

    for k, v in update_dict.items():
        setattr(cat, k, v)

    await session.commit()
    await session.refresh(cat)
    return cat


async def delete_category(
    session: AsyncSession,
    cat_id: str,
    reassign_to_id: Optional[str] = None
) -> None:
    """
    Safely delete a category with relation guard.
    If knowledge items exist:
      - If reassign_to_id is None -> raise ValueError (guard violation)
      - If reassign_to_id == 'unclassified' -> reassign knowledge items to NULL
      - If reassign_to_id is a valid category ID -> reassign knowledge items to target
    """
    cat = await get_category_by_id(session, cat_id)
    if not cat:
        raise ValueError(f"分类不存在: {cat_id}")

    # Check related knowledge items count
    count_stmt = select(func.count(KnowledgeItem.id)).where(KnowledgeItem.category_id == cat_id)
    count_res = await session.execute(count_stmt)
    knowledge_count = count_res.scalar() or 0

    if knowledge_count > 0:
        if not reassign_to_id:
            raise ValueError(
                f"分类 '{cat.name}' 下仍有 {knowledge_count} 篇知识点，无法直接删除。"
                "请指定目标分类迁移，或设置为未分类 ('unclassified')。"
            )

        if reassign_to_id.lower() == "unclassified":
            await session.execute(
                update(KnowledgeItem)
                .where(KnowledgeItem.category_id == cat_id)
                .values(category_id=None)
            )
        else:
            target_cat = await get_category_by_id(session, reassign_to_id)
            if not target_cat:
                raise ValueError(f"目标迁移分类不存在: {reassign_to_id}")
            await session.execute(
                update(KnowledgeItem)
                .where(KnowledgeItem.category_id == cat_id)
                .values(category_id=reassign_to_id)
            )

    # Reparent subcategories to cat.parent_id so children are not orphaned
    await session.execute(
        update(Category)
        .where(Category.parent_id == cat_id)
        .values(parent_id=cat.parent_id)
    )

    # Delete the category
    await session.execute(delete(Category).where(Category.id == cat_id))
    await session.commit()
