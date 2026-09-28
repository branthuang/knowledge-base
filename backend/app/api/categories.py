from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryTreeNode,
    CategoryDeleteRequest,
)
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
async def list_categories(
    status: Optional[str] = Query(None, description="按状态过滤: active / inactive"),
    session: AsyncSession = Depends(get_db_session),
):
    """获取所有分类列表及关联知识数量。"""
    return await category_service.list_categories(session, status=status)


@router.get("/tree", response_model=List[CategoryTreeNode])
async def get_category_tree(
    status: Optional[str] = Query(None, description="按状态过滤: active / inactive"),
    session: AsyncSession = Depends(get_db_session),
):
    """获取层级分类树形结构。"""
    return await category_service.get_category_tree(session, status=status)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取指定分类详情。"""
    cat = await category_service.get_category_by_id(session, category_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类未找到")
    return CategoryResponse.model_validate(cat)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """创建新分类。"""
    try:
        cat = await category_service.create_category(session, data)
        return CategoryResponse.model_validate(cat)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    data: CategoryUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    """更新指定分类。"""
    try:
        cat = await category_service.update_category(session, category_id, data)
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类未找到")
        return CategoryResponse.model_validate(cat)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    reassign_to_id: Optional[str] = Query(None, description="目标分类ID，或 'unclassified'"),
    session: AsyncSession = Depends(get_db_session),
):
    """安全删除分类，若分类下存在知识点必须指定迁移分类或设置为未分类。"""
    try:
        await category_service.delete_category(session, category_id, reassign_to_id=reassign_to_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
