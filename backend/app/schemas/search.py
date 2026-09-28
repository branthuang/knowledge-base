from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.tag import TagResponse


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200, description="搜索关键词或自然语言问题")
    category_id: Optional[str] = Field(default=None, description="分类ID（支持级联包含子分类）")
    tag_ids: Optional[List[str]] = Field(default=None, description="标签ID筛选列表")
    source_type: Optional[str] = Field(default=None, description="来源类型（manual, ai_search, import, web_clip）")
    favorite: Optional[bool] = Field(default=None, description="是否仅检索收藏")
    start_date: Optional[datetime] = Field(default=None, description="起始更新时间")
    end_date: Optional[datetime] = Field(default=None, description="截止更新时间")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=50, description="每页条数")
    minimum_score: float = Field(default=0.60, ge=0.0, le=1.0, description="充分性评估最低阈值")


class SearchHitItem(BaseModel):
    id: str = Field(description="知识点ID")
    title: str = Field(description="知识点标题")
    summary: Optional[str] = Field(default=None, description="知识点摘要")
    category_id: Optional[str] = Field(default=None, description="分类ID")
    category_name: Optional[str] = Field(default=None, description="分类名称")
    tags: List[TagResponse] = Field(default_factory=list, description="关联标签列表")
    source_type: str = Field(description="来源类型")
    favorite: bool = Field(description="是否收藏")
    score: float = Field(description="综合融合评分 [0.0, 1.0]")
    keyword_score: float = Field(description="关键词归一化评分 [0.0, 1.0]")
    vector_score: float = Field(description="向量语义相似度评分 [0.0, 1.0]")
    best_snippet: str = Field(description="最佳匹配内容片段")
    matched_block_id: Optional[str] = Field(default=None, description="命中的内容块ID")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    query: str = Field(description="搜索关键词")
    total: int = Field(description="总命中知识点数量")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页条数")
    is_sufficient: bool = Field(description="本地知识是否充足（Top-1 score >= minimum_score）")
    ai_search_suggested: bool = Field(description="是否推荐向 AI / 公网提问")
    ai_search_prompt: Optional[str] = Field(default=None, description="AI 搜索引导提示语")
    items: List[SearchHitItem] = Field(default_factory=list, description="检索结果列表")
