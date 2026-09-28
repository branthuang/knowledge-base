import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.schemas.optimization import (
    OptimizationRequest,
    OptimizationResponse,
)
from app.services.optimization_service import default_optimization_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimization", tags=["AI Optimization"])


@router.post("/polish", response_model=OptimizationResponse, summary="执行知识内容 AI 一键润色优化")
async def polish_content_endpoint(
    payload: OptimizationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> OptimizationResponse:
    """
    知识编辑器 AI 一键润色：
    - 支持简洁易懂（默认）、结构化、专业规范与仅纠错 4 种优化模式；
    - 严格保持代码块逐字不变、关键数据与 URL 不变；
    - 绝不编造外部事实，生成 BlockItem 结构化草稿树以供用户双栏比对确认；
    - 智能分析并给出推荐分类与标签建议。
    """
    try:
        return await default_optimization_service.optimize_content(session, payload)
    except Exception as e:
        logger.error("Content optimization failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI 优化执行失败: {str(e)}")
