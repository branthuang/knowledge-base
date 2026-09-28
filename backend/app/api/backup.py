import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.services.backup_service import default_backup_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backup", tags=["Backup & Restore"])


@router.get("/export", summary="导出全量知识库标准 ZIP 归档备份包")
async def export_backup_endpoint(
    session: AsyncSession = Depends(get_db_session),
):
    """
    全量数据打包备份导出：
    1. 导出完整 categories, tags, knowledge_items, knowledge_tags, sources 到 data.json；
    2. 生成包含数据统计与 SHA-256 签名校验和的 manifest.json；
    3. 打包为标准 ZIP 字节流并下载。
    """
    try:
        zip_bytes = await default_backup_service.export_full_backup(session)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"knowledge_backup_{timestamp}.zip"
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error("Failed to export backup: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出备份失败: {str(e)}")


@router.post("/restore", summary="上传并原子恢复全量知识库备份包")
async def restore_backup_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """
    全量备份恢复：
    1. 校验 ZIP 内 manifest.json 与 data.json 的存在性；
    2. 计算 data.json 真实哈希并严格比对 checksum_sha256；
    3. 原子性事务导入各表数据；
    4. 自动全量重建派生文本与向量索引。
    """
    try:
        zip_bytes = await request.body()
        if not zip_bytes:
            raise ValueError("上传的备份包数据为空")
        return await default_backup_service.restore_full_backup(session, zip_bytes)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("Failed to restore backup: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"恢复备份失败: {str(e)}")


@router.get("/export/markdown/{knowledge_id}", summary="单篇知识导出为标准 Markdown")
async def export_markdown_endpoint(
    knowledge_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """单篇知识无损导出为标准 GitHub Flavored Markdown 文本。"""
    try:
        md_text = await default_backup_service.export_single_markdown(session, knowledge_id)
        filename = f"knowledge_{knowledge_id}.md"
        return Response(
            content=md_text,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error("Failed to export single markdown: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出 Markdown 失败: {str(e)}")
