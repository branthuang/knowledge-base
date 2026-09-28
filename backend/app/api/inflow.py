import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.schemas.inflow import (
    InflowPreviewRequest,
    InflowPreviewResponse,
    InflowConfirmRequest,
)
from app.schemas.knowledge import KnowledgeDetailResponse, SourceInfoResponse
from app.schemas.tag import TagResponse
from app.services.inflow_service import default_inflow_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inflow", tags=["Knowledge Inflow"])


@router.post("/preview", response_model=InflowPreviewResponse, summary="生成入库结构化预览与防重检测")
async def generate_inflow_preview_endpoint(
    payload: InflowPreviewRequest,
    session: AsyncSession = Depends(get_db_session),
) -> InflowPreviewResponse:
    """
    一键生成知识入库预览：
    1. 将 AI 回答文本自动解析为编辑器 Block 结构树；
    2. 将公网引用格式化为参考资料引用块并提取为来源项；
    3. 智能推荐标题、摘要、分类与标签；
    4. 库内高相似度检测（防重告警）。
    """
    try:
        return await default_inflow_service.generate_preview(session, payload)
    except Exception as e:
        logger.error("Failed to generate inflow preview: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成入库预览失败: {str(e)}")


@router.post("/confirm", response_model=KnowledgeDetailResponse, status_code=status.HTTP_201_CREATED, summary="确认入库落盘与向量索引构建")
async def confirm_inflow_endpoint(
    payload: InflowConfirmRequest,
    session: AsyncSession = Depends(get_db_session),
) -> KnowledgeDetailResponse:
    """
    确认知识沉淀入库：
    1. 支持创建为新知识（create_new）或覆盖合并至已有相似知识（update_existing）；
    2. 保存结构化 Blocks 内容与来源引用关联；
    3. 反向回填搜索会话 saved_knowledge_id；
    4. 触发派生分块与向量索引生成。
    """
    try:
        item = await default_inflow_service.confirm_inflow(session, payload)
        if not item:
            raise HTTPException(status_code=500, detail="知识入库失败")

        return KnowledgeDetailResponse(
            id=item.id,
            title=item.title,
            summary=item.summary,
            category_id=item.category_id,
            category_name=item.category.name if item.category else None,
            tags=[TagResponse.model_validate(t) for t in item.tags] if item.tags else [],
            source_type=item.source_type,
            status=item.status,
            favorite=item.favorite,
            index_status=item.index_status,
            created_at=item.created_at,
            updated_at=item.updated_at,
            blocks_json=item.blocks_json,
            plain_text=item.plain_text,
            sources=[SourceInfoResponse.model_validate(s) for s in item.sources] if item.sources else [],
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("Failed to confirm inflow: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"知识入库失败: {str(e)}")
