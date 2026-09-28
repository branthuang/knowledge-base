from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class WorkbenchStatsResponse(BaseModel):
    total_knowledge: int = Field(description="知识点总篇数（排除回收站）")
    total_categories: int = Field(description="启用分类总数")
    total_tags: int = Field(description="标签总数")
    monthly_added_count: int = Field(description="本月新增知识数")
    ai_inflow_count: int = Field(description="由 AI 搜索沉淀入库的知识总数")

    model_config = ConfigDict(from_attributes=True)


class RecentKnowledgeItem(BaseModel):
    id: str = Field(description="知识点ID")
    title: str = Field(description="标题")
    summary: Optional[str] = Field(default=None, description="摘要")
    category_id: Optional[str] = Field(default=None, description="分类ID")
    category_name: Optional[str] = Field(default=None, description="分类名称")
    status: str = Field(description="状态: published, draft, archived")
    updated_at: datetime = Field(description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class PendingReviewDraftItem(BaseModel):
    id: str = Field(description="知识点ID")
    title: str = Field(description="标题")
    summary: Optional[str] = Field(default=None, description="摘要")
    category_name: Optional[str] = Field(default=None, description="分类名称")
    source_type: str = Field(description="来源类型（通常为 ai_search）")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class RecentSearchSessionItem(BaseModel):
    id: str = Field(description="搜索会话ID")
    query: str = Field(description="搜索问题")
    mode: str = Field(description="搜索模式")
    saved_knowledge_id: Optional[str] = Field(default=None, description="沉淀关联的知识ID")
    created_at: datetime = Field(description="会话创建时间")

    model_config = ConfigDict(from_attributes=True)


class PopularTagItem(BaseModel):
    id: str = Field(description="标签ID")
    name: str = Field(description="标签名称")
    color: Optional[str] = Field(default=None, description="颜色标识")
    knowledge_count: int = Field(default=0, description="关联知识数量")

    model_config = ConfigDict(from_attributes=True)


class WorkbenchActivitiesResponse(BaseModel):
    recent_knowledge: List[RecentKnowledgeItem] = Field(default_factory=list, description="最近编辑/访问知识列表")
    pending_drafts: List[PendingReviewDraftItem] = Field(default_factory=list, description="待整理的 AI 沉淀草稿列表")
    pending_drafts_count: int = Field(default=0, description="待整理草稿总数量")
    recent_searches: List[RecentSearchSessionItem] = Field(default_factory=list, description="近期搜索历史列表")
    popular_tags: List[PopularTagItem] = Field(default_factory=list, description="常用高频标签列表")
