from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.schemas.knowledge import (
    KnowledgeCreate,
    KnowledgeUpdate,
    KnowledgeDetailResponse,
    PaginatedKnowledgeResponse,
    SourceInfoResponse,
)
from app.schemas.tag import TagResponse
from app.services import knowledge_service

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.get("", response_model=PaginatedKnowledgeResponse)
async def list_knowledge(
    category_id: Optional[str] = Query(None, description="分类 ID"),
    cascade_category: bool = Query(True, description="是否级联包含子分类"),
    tag_ids: Optional[List[str]] = Query(None, description="标签 ID 列表"),
    source_type: Optional[str] = Query(None, description="来源类型"),
    status: Optional[str] = Query(None, description="状态: draft, published, archived"),
    favorite: Optional[bool] = Query(None, description="是否收藏/置顶"),
    keyword: Optional[str] = Query(None, description="标题/正文关键词快速匹配"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    session: AsyncSession = Depends(get_db_session),
):
    """获取知识点列表（多维组合过滤，支持分类级联与分页）。"""
    return await knowledge_service.list_knowledge(
        session=session,
        status=status,
        category_id=category_id,
        cascade_category=cascade_category,
        tag_ids=tag_ids,
        source_type=source_type,
        favorite=favorite,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )


@router.get("/trash/list", response_model=PaginatedKnowledgeResponse)
async def list_trash(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """查看回收站中的知识点列表。"""
    return await knowledge_service.list_knowledge(
        session=session,
        status="trashed",
        page=page,
        page_size=page_size,
    )


@router.get("/{knowledge_id}", response_model=KnowledgeDetailResponse)
async def get_knowledge(
    knowledge_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取单篇知识点详情（包含块数据、派生纯文本、关联标签与来源信息）。"""
    item = await knowledge_service.get_knowledge_by_id(session, knowledge_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识点未找到")

    return KnowledgeDetailResponse(
        id=item.id,
        title=item.title,
        summary=item.summary,
        category_id=item.category_id,
        category_name=item.category.name if item.category else None,
        tags=[TagResponse.model_validate(t) for t in item.tags],
        source_type=item.source_type,
        status=item.status,
        favorite=item.favorite,
        index_status=item.index_status,
        created_at=item.created_at,
        updated_at=item.updated_at,
        blocks_json=item.blocks_json,
        plain_text=item.plain_text,
        sources=[SourceInfoResponse.model_validate(s) for s in item.sources],
    )


@router.post("", response_model=KnowledgeDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge(
    data: KnowledgeCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """创建新知识点或暂存草稿（自动提取派生纯文本，绑定标签与来源）。"""
    try:
        item = await knowledge_service.create_knowledge(session, data)
        return KnowledgeDetailResponse(
            id=item.id,
            title=item.title,
            summary=item.summary,
            category_id=item.category_id,
            category_name=item.category.name if item.category else None,
            tags=[TagResponse.model_validate(t) for t in item.tags],
            source_type=item.source_type,
            status=item.status,
            favorite=item.favorite,
            index_status=item.index_status,
            created_at=item.created_at,
            updated_at=item.updated_at,
            blocks_json=item.blocks_json,
            plain_text=item.plain_text,
            sources=[SourceInfoResponse.model_validate(s) for s in item.sources],
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.put("/{knowledge_id}", response_model=KnowledgeDetailResponse)
async def update_knowledge(
    knowledge_id: str,
    data: KnowledgeUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    """更新知识点正文块或元数据（若修改块内容自动重新提取纯文本并标记索引待更新）。"""
    item = await knowledge_service.update_knowledge(session, knowledge_id, data)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识点未找到")

    return KnowledgeDetailResponse(
        id=item.id,
        title=item.title,
        summary=item.summary,
        category_id=item.category_id,
        category_name=item.category.name if item.category else None,
        tags=[TagResponse.model_validate(t) for t in item.tags],
        source_type=item.source_type,
        status=item.status,
        favorite=item.favorite,
        index_status=item.index_status,
        created_at=item.created_at,
        updated_at=item.updated_at,
        blocks_json=item.blocks_json,
        plain_text=item.plain_text,
        sources=[SourceInfoResponse.model_validate(s) for s in item.sources],
    )


@router.delete("/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def move_to_trash(
    knowledge_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """软删除：将知识点移入回收站。"""
    success = await knowledge_service.move_to_trash(session, knowledge_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识点未找到")


@router.post("/{knowledge_id}/restore", status_code=status.HTTP_200_OK)
async def restore_from_trash(
    knowledge_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """从回收站恢复知识点。"""
    success = await knowledge_service.restore_from_trash(session, knowledge_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识点未找到或不在回收站中")
    return {"message": "知识点已成功恢复"}


@router.delete("/{knowledge_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanent_delete(
    knowledge_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """物理删除：从系统中彻底移除该知识点及其所有关联数据。"""
    success = await knowledge_service.permanent_delete(session, knowledge_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识点未找到")
