from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.schemas.tag import (
    TagCreate,
    TagUpdate,
    TagResponse,
    TagWithStatsResponse,
    TagMergeRequest,
)
from app.services import tag_service

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("", response_model=List[TagWithStatsResponse])
async def list_tags(session: AsyncSession = Depends(get_db_session)):
    """获取所有标签及其关联知识数量与最近使用时间。"""
    return await tag_service.list_tags_with_stats(session)


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: str, session: AsyncSession = Depends(get_db_session)):
    """获取单个标签详情。"""
    tag = await tag_service.get_tag_by_id(session, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签未找到")
    return TagResponse.model_validate(tag)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(data: TagCreate, session: AsyncSession = Depends(get_db_session)):
    """创建新标签。"""
    try:
        tag = await tag_service.create_tag(session, data)
        return TagResponse.model_validate(tag)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: str, data: TagUpdate, session: AsyncSession = Depends(get_db_session)):
    """更新指定标签信息。"""
    try:
        tag = await tag_service.update_tag(session, tag_id, data)
        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签未找到")
        return TagResponse.model_validate(tag)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: str, session: AsyncSession = Depends(get_db_session)):
    """删除标签并级联清理关联绑定关系。"""
    deleted = await tag_service.delete_tag(session, tag_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签未找到")


@router.post("/merge", response_model=TagResponse)
async def merge_tags(data: TagMergeRequest, session: AsyncSession = Depends(get_db_session)):
    """将源标签合并至目标标签，自动迁移所有知识关联并去重，随后删除源标签。"""
    try:
        return await tag_service.merge_tags(session, data.source_tag_id, data.target_tag_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
