import logging
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import default_search_service
from app.services.index_service import default_index_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Hybrid Search"])


@router.post("", response_model=SearchResponse, summary="混合检索（POST 请求体）")
async def search_post(
    payload: SearchRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SearchResponse:
    """
    统一混合检索接口：
    1. 整合关键词检索 + 向量语义检索双路召回。
    2. 支持级联分类、多标签、来源类型等结构化过滤。
    3. 综合归一化融合评分，聚合知识点并提取最佳摘要片段。
    4. 评估本地知识充分性（is_sufficient），不足时输出 AI 搜索引导。
    """
    try:
        return await default_search_service.search(session, payload)
    except Exception as e:
        logger.error("Search execution failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"检索服务异常: {str(e)}")


@router.get("", response_model=SearchResponse, summary="混合检索（GET 查询参数）")
async def search_get(
    q: str = Query(..., min_length=1, max_length=200, description="搜索关键词"),
    category_id: Optional[str] = Query(None, description="分类ID（支持级联包含子分类）"),
    tag_ids: Optional[List[str]] = Query(None, description="标签ID筛选列表"),
    source_type: Optional[str] = Query(None, description="来源类型"),
    favorite: Optional[bool] = Query(None, description="是否仅检索收藏"),
    start_date: Optional[datetime] = Query(None, description="起始更新时间"),
    end_date: Optional[datetime] = Query(None, description="截止更新时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页条数"),
    minimum_score: float = Query(0.60, ge=0.0, le=1.0, description="充分性评估最低阈值"),
    session: AsyncSession = Depends(get_db_session),
) -> SearchResponse:
    """GET 方式混合检索，方便地址栏直接传参或书签分享。"""
    payload = SearchRequest(
        query=q,
        category_id=category_id,
        tag_ids=tag_ids,
        source_type=source_type,
        favorite=favorite,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
        minimum_score=minimum_score,
    )
    try:
        return await default_search_service.search(session, payload)
    except Exception as e:
        logger.error("Search execution failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"检索服务异常: {str(e)}")


@router.post("/reindex", summary="全量重建知识向量索引")
async def trigger_reindex(
    session: AsyncSession = Depends(get_db_session),
):
    """触发全量知识点文本分块与向量索引重建。"""
    try:
        summary = await default_index_service.reindex_all(session)
        return {"status": "success", "message": "全量重建索引完成", "metrics": summary}
    except Exception as e:
        logger.error("Reindex failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"重建索引失败: {str(e)}")
