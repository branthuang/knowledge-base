from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.tag import TagResponse


class SourceInfoCreate(BaseModel):
    type: str = Field(default="manual", description="来源类型: manual, ai_search, url, file")
    url: Optional[str] = Field(default=None, description="来源 URL")
    title: Optional[str] = Field(default=None, description="来源标题")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="来源元数据，如原始 query、AI provider 等")


class SourceInfoResponse(SourceInfoCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255, description="知识点标题")
    summary: Optional[str] = Field(default=None, description="摘要")
    blocks_json: List[Any] = Field(default_factory=list, description="结构化块数据集合")
    category_id: Optional[str] = Field(default=None, description="主分类 ID")
    tag_ids: List[str] = Field(default_factory=list, description="绑定的标签 ID 列表")
    source_type: str = Field(default="manual", description="来源类型: manual, ai_search, import, web_clip")
    status: str = Field(default="draft", description="初始状态: draft, published, archived")
    favorite: bool = Field(default=False, description="是否收藏/置顶")
    sources: List[SourceInfoCreate] = Field(default_factory=list, description="来源信息列表")


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    summary: Optional[str] = None
    blocks_json: Optional[List[Any]] = None
    category_id: Optional[str] = None
    tag_ids: Optional[List[str]] = None
    status: Optional[str] = None
    favorite: Optional[bool] = None
    sources: Optional[List[SourceInfoCreate]] = None


class KnowledgeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    summary: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    tags: List[TagResponse] = Field(default_factory=list)
    source_type: str
    status: str
    favorite: bool
    index_status: str
    created_at: datetime
    updated_at: datetime


class KnowledgeDetailResponse(KnowledgeListItem):
    model_config = ConfigDict(from_attributes=True)

    blocks_json: List[Any] = Field(default_factory=list)
    plain_text: str = ""
    sources: List[SourceInfoResponse] = Field(default_factory=list)


class PaginatedKnowledgeResponse(BaseModel):
    items: List[KnowledgeListItem]
    total: int
    page: int
    page_size: int
    pages: int
