import logging
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category

logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = [
    {
        "name": "技术类",
        "description": "技术开发、系统架构、基础设施与工程实践知识",
        "icon": "code",
        "color": "#2563EB",  # Blue
        "sort_order": 1,
    },
    {
        "name": "公司知识类",
        "description": "公司业务规则、流程规范、团队协作与制度知识",
        "icon": "building",
        "color": "#059669",  # Green
        "sort_order": 2,
    },
]


async def seed_default_categories(session: AsyncSession) -> List[Category]:
    """Idempotently seed default top-level categories if they do not already exist."""
    seeded: List[Category] = []
    for item in DEFAULT_CATEGORIES:
        stmt = select(Category).where(Category.name == item["name"])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is None:
            cat = Category(
                name=item["name"],
                description=item["description"],
                icon=item["icon"],
                color=item["color"],
                sort_order=item["sort_order"],
                status="active",
            )
            session.add(cat)
            seeded.append(cat)
            logger.info("Seeded default category: %s", item["name"])
        else:
            seeded.append(existing)

    await session.commit()
    return seeded
