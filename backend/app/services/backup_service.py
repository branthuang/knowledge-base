import io
import json
import zipfile
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.models.tag import Tag, KnowledgeTag
from app.models.knowledge import KnowledgeItem
from app.models.source import KnowledgeSource
from app.services.block_parser import blocks_to_markdown
from app.services.knowledge_service import get_knowledge_by_id
from app.services.index_service import IndexService, default_index_service

logger = logging.getLogger(__name__)


class BackupService:
    """
    Data Backup & Restore Domain Service:
    1. Full backup export: self-contained ZIP containing manifest.json with SHA-256 and data.json.
    2. Atomic full backup restore: verifies checksum, restores DB records, and triggers index rebuild.
    3. Single knowledge export: converts structured knowledge to standardized Markdown format.
    """

    def __init__(self, index_svc: Optional[IndexService] = None):
        self.index_service = index_svc or default_index_service

    async def export_full_backup(self, session: AsyncSession) -> bytes:
        # 1. Categories
        cat_res = await session.execute(select(Category).order_by(Category.sort_order.asc()))
        categories_data = [
            {
                "id": c.id,
                "name": c.name,
                "parent_id": c.parent_id,
                "description": c.description,
                "icon": c.icon,
                "color": c.color,
                "sort_order": c.sort_order,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in cat_res.scalars().all()
        ]

        # 2. Tags
        tag_res = await session.execute(select(Tag).order_by(Tag.name.asc()))
        tags_data = [
            {
                "id": t.id,
                "name": t.name,
                "parent_id": t.parent_id,
                "description": t.description,
                "color": t.color,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in tag_res.scalars().all()
        ]

        # 3. Knowledge Items
        k_res = await session.execute(select(KnowledgeItem))
        knowledge_data = [
            {
                "id": k.id,
                "title": k.title,
                "summary": k.summary,
                "blocks_json": k.blocks_json,
                "plain_text": k.plain_text,
                "category_id": k.category_id,
                "source_type": k.source_type,
                "status": k.status,
                "favorite": k.favorite,
                "index_status": k.index_status,
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "updated_at": k.updated_at.isoformat() if k.updated_at else None,
            }
            for k in k_res.scalars().all()
        ]

        # 4. Knowledge Tags associations
        kt_res = await session.execute(select(KnowledgeTag.knowledge_id, KnowledgeTag.tag_id))
        kt_data = [{"knowledge_id": row[0], "tag_id": row[1]} for row in kt_res.all()]

        # 5. Sources
        src_res = await session.execute(select(KnowledgeSource))
        sources_data = [
            {
                "id": s.id,
                "knowledge_id": s.knowledge_id,
                "type": s.type,
                "url": s.url,
                "title": s.title,
                "metadata_json": s.metadata_json,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in src_res.scalars().all()
        ]

        # Assemble data.json
        data_dict = {
            "categories": categories_data,
            "tags": tags_data,
            "knowledge_items": knowledge_data,
            "knowledge_tags": kt_data,
            "sources": sources_data,
        }
        data_json_bytes = json.dumps(data_dict, ensure_ascii=False, indent=2).encode("utf-8")
        checksum = hashlib.sha256(data_json_bytes).hexdigest()

        # Assemble manifest.json
        manifest_dict = {
            "schema_version": "1.0",
            "app_name": "KnowledgeBase",
            "app_version": "0.1.0",
            "exported_at": datetime.now().isoformat(),
            "stats": {
                "categories_count": len(categories_data),
                "tags_count": len(tags_data),
                "knowledge_count": len(knowledge_data),
                "sources_count": len(sources_data),
            },
            "checksum_sha256": checksum,
        }
        manifest_bytes = json.dumps(manifest_dict, ensure_ascii=False, indent=2).encode("utf-8")

        # Package into ZIP in-memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", manifest_bytes)
            zf.writestr("data.json", data_json_bytes)

        return zip_buffer.getvalue()

    async def restore_full_backup(
        self,
        session: AsyncSession,
        zip_bytes: bytes,
    ) -> Dict[str, Any]:
        """Verify checksum, restore records into database, and trigger index rebuild."""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
                if "manifest.json" not in zf.namelist() or "data.json" not in zf.namelist():
                    raise ValueError("备份包格式非法：压缩包内必须包含 manifest.json 与 data.json")

                manifest_raw = zf.read("manifest.json")
                data_raw = zf.read("data.json")
        except zipfile.BadZipFile:
            raise ValueError("上传的文件不是合法的 ZIP 压缩包")

        manifest = json.loads(manifest_raw)
        expected_sha256 = manifest.get("checksum_sha256")
        actual_sha256 = hashlib.sha256(data_raw).hexdigest()

        if expected_sha256 and expected_sha256 != actual_sha256:
            raise ValueError(
                f"备份包完整性校验失败：校验和不匹配（期望: {expected_sha256}, 实际: {actual_sha256}）"
            )

        data = json.loads(data_raw)

        # 1. Restore Categories
        restored_cats = 0
        for c in data.get("categories", []):
            existing = await session.get(Category, c["id"])
            if not existing:
                cat = Category(
                    id=c["id"],
                    name=c["name"],
                    parent_id=c.get("parent_id"),
                    description=c.get("description"),
                    icon=c.get("icon"),
                    color=c.get("color"),
                    sort_order=c.get("sort_order", 0),
                    status=c.get("status", "active"),
                )
                session.add(cat)
                restored_cats += 1

        # 2. Restore Tags
        restored_tags = 0
        for t in data.get("tags", []):
            existing = await session.get(Tag, t["id"])
            if not existing:
                tag = Tag(
                    id=t["id"],
                    name=t["name"],
                    parent_id=t.get("parent_id"),
                    description=t.get("description"),
                    color=t.get("color"),
                )
                session.add(tag)
                restored_tags += 1

        await session.flush()

        # 3. Restore Knowledge Items
        restored_k = 0
        for k in data.get("knowledge_items", []):
            existing = await session.get(KnowledgeItem, k["id"])
            if not existing:
                item = KnowledgeItem(
                    id=k["id"],
                    title=k["title"],
                    summary=k.get("summary"),
                    blocks_json=k.get("blocks_json", []),
                    plain_text=k.get("plain_text", ""),
                    category_id=k.get("category_id"),
                    source_type=k.get("source_type", "manual"),
                    status=k.get("status", "published"),
                    favorite=k.get("favorite", False),
                    index_status="pending",
                )
                session.add(item)
                restored_k += 1

        await session.flush()

        # 4. Restore Knowledge Tags
        for kt in data.get("knowledge_tags", []):
            kid = kt.get("knowledge_id")
            tid = kt.get("tag_id")
            if kid and tid:
                check_stmt = select(KnowledgeTag).where(
                    KnowledgeTag.knowledge_id == kid, KnowledgeTag.tag_id == tid
                )
                res = await session.execute(check_stmt)
                if not res.scalar_one_or_none():
                    session.add(KnowledgeTag(knowledge_id=kid, tag_id=tid))

        # 5. Restore Sources
        restored_sources = 0
        for s in data.get("sources", []):
            existing = await session.get(KnowledgeSource, s["id"])
            if not existing:
                src = KnowledgeSource(
                    id=s["id"],
                    knowledge_id=s["knowledge_id"],
                    type=s.get("type", "manual"),
                    url=s.get("url"),
                    title=s.get("title"),
                    metadata_json=s.get("metadata_json", {}),
                )
                session.add(src)
                restored_sources += 1

        await session.commit()

        # 6. Rebuild Indexes
        reindex_summary = await self.index_service.reindex_all(session)

        return {
            "status": "success",
            "manifest": manifest,
            "restored_counts": {
                "categories": restored_cats,
                "tags": restored_tags,
                "knowledge_items": restored_k,
                "sources": restored_sources,
            },
            "reindex_metrics": reindex_summary,
        }

    async def export_single_markdown(self, session: AsyncSession, knowledge_id: str) -> str:
        """Export single knowledge item to clean Markdown string with metadata and sources."""
        item = await get_knowledge_by_id(session, knowledge_id)
        if not item:
            raise ValueError(f"知识点不存在: {knowledge_id}")

        cat_name = item.category.name if item.category else "未分类"
        tag_names = ", ".join(t.name for t in item.tags) if item.tags else "无"
        updated_str = item.updated_at.strftime("%Y-%m-%d %H:%M:%S") if item.updated_at else ""

        body_md = ""
        if item.blocks_json and isinstance(item.blocks_json, list) and len(item.blocks_json) > 0:
            body_md = blocks_to_markdown(item.blocks_json)
        else:
            body_md = item.plain_text or ""

        md_parts = [
            f"# {item.title}\n",
            f"> **分类**: {cat_name} | **标签**: {tag_names} | **更新时间**: {updated_str}\n",
        ]

        if item.summary:
            md_parts.append(f"**摘要**: {item.summary}\n")

        md_parts.append("---\n")
        md_parts.append(body_md)

        if item.sources:
            md_parts.append("\n\n---\n## 参考资料与来源\n")
            for s in item.sources:
                title = s.title or "外部来源"
                url = s.url or ""
                if url:
                    md_parts.append(f"- [{title}]({url})")
                else:
                    md_parts.append(f"- {title}")

        return "\n".join(md_parts)


default_backup_service = BackupService()
