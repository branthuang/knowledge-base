import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.schemas.workbench import (
    WorkbenchStatsResponse,
    WorkbenchActivitiesResponse,
)
from app.services.workbench_service import default_workbench_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workbench", tags=["Workbench Dashboard"])


@router.get("/stats", response_model=WorkbenchStatsResponse, summary="获取工作台核心统计指标")
async def get_workbench_stats_endpoint(
    session: AsyncSession = Depends(get_db_session),
) -> WorkbenchStatsResponse:
    """
    获取知识库 5 项宏观指标：
    1. 知识点总数（非回收站）；
    2. 分类总数；
    3. 标签总数；
    4. 本月新增知识数；
    5. 由 AI 搜索转化沉淀的知识总数。
    """
    try:
        return await default_workbench_service.get_workbench_stats(session)
    except Exception as e:
        logger.error("Failed to load workbench stats: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取工作台统计失败: {str(e)}")


@router.get("/activities", response_model=WorkbenchActivitiesResponse, summary="获取工作台最近动态与待整理事项")
async def get_workbench_activities_endpoint(
    session: AsyncSession = Depends(get_db_session),
) -> WorkbenchActivitiesResponse:
    """
    获取工作台动态流转总览：
    1. 最近编辑或访问的知识点；
    2. 待整理的 AI 沉淀草稿（提醒徽章及列表）；
    3. 近期搜索历史；
    4. 常用高频标签快捷入口。
    """
    try:
        return await default_workbench_service.get_workbench_activities(session)
    except Exception as e:
        logger.error("Failed to load workbench activities: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取工作台动态失败: {str(e)}")
