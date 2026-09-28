import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.schemas.ai_search import (
    AISearchRequest,
    AISearchResponse,
    SearchSessionListItem,
    SearchSessionDetailResponse,
)
from app.services.ai_search_service import default_ai_search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-search", tags=["AI Search & Sessions"])


@router.post("", response_model=AISearchResponse, summary="发起 AI 增强搜索与问答")
async def execute_ai_search_endpoint(
    payload: AISearchRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AISearchResponse:
    """
    统一 AI 增强搜索入口：
    - 支持 knowledge_first, external_supplement, knowledge_only, direct_ai 四种模式；
    - 结合本地知识充分性评估与公网检索；
    - 输出大模型综合回答、内部知识引用及公网可追溯链接；
    - 自动持久化搜索快照至 search_sessions。
    """
    try:
        return await default_ai_search_service.execute_ai_search(session, payload)
    except Exception as e:
        logger.error("AI Search execution failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI 搜索服务异常: {str(e)}")


@router.get("/sessions", response_model=List[SearchSessionListItem], summary="获取搜索历史会话列表")
async def list_search_sessions_endpoint(
    limit: int = Query(20, ge=1, le=100, description="每页条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    session: AsyncSession = Depends(get_db_session),
) -> List[SearchSessionListItem]:
    """查询搜索历史记录，按时间倒序排列。"""
    try:
        return await default_ai_search_service.list_sessions(session, limit=limit, offset=offset)
    except Exception as e:
        logger.error("Failed to list search sessions: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取搜索历史失败: {str(e)}")


@router.get("/sessions/{session_id}", response_model=SearchSessionDetailResponse, summary="获取搜索会话详情")
async def get_search_session_endpoint(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> SearchSessionDetailResponse:
    """获取单次搜索会话的完整快照（包含当时命中的本地结果、公网引用、AI回答全文及沉淀状态）。"""
    detail = await default_ai_search_service.get_session(session, session_id)
    if not detail:
        raise HTTPException(status_code=404, detail="搜索会话不存在")
    return detail
