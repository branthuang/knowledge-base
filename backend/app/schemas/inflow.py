from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.block import BlockItem


class InflowAction(str, Enum):
    CREATE_NEW = "create_new"          # 坚持作为新知识入库
    UPDATE_EXISTING = "update_existing"  # 覆盖/更新已有相似知识


class InflowSourceItem(BaseModel):
    type: str = Field(default="ai_search", description="来源类型（url, ai_search, paper等）")
    url: Optional[str] = Field(default=None, description="来源链接")
    title: Optional[str] = Field(default=None, description="来源标题")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class SimilarKnowledgeCandidate(BaseModel):
    id: str = Field(description="库内已有知识ID")
    title: str = Field(description="已有知识标题")
    snippet: str = Field(description="匹配摘要或片段")
    similarity_score: float = Field(description="相似度分值 [0.0, 1.0]")
    category_name: Optional[str] = Field(default=None, description="已有知识所属分类")
    updated_at: datetime = Field(description="最近更新时间")


class InflowPreviewRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="来源搜索会话ID（优先从会话加载）")
    query: Optional[str] = Field(default=None, description="原始问题（若未提供 session_id 时传入）")
    content_markdown: Optional[str] = Field(default=None, description="Markdown 正文（若未提供 session_id 时传入）")
    citations: Optional[List[Dict[str, Any]]] = Field(default=None, description="公网参考引用列表")


class InflowPreviewResponse(BaseModel):
    session_id: Optional[str] = Field(default=None, description="关联的搜索会话ID")
    recommended_title: str = Field(description="智能推荐标题")
    recommended_summary: str = Field(description="智能推荐摘要草稿")
    blocks: List[BlockItem] = Field(default_factory=list, description="解析组装的编辑器内容块列表")
    recommended_category_id: Optional[str] = Field(default=None, description="推荐归属分类ID")
    recommended_category_name: Optional[str] = Field(default=None, description="推荐归属分类名称")
    recommended_tag_ids: List[str] = Field(default_factory=list, description="推荐标签ID列表")
    recommended_tag_names: List[str] = Field(default_factory=list, description="推荐标签名称列表")
    sources: List[InflowSourceItem] = Field(default_factory=list, description="溯源来源列表")
    has_similar_knowledge: bool = Field(default=False, description="是否命中高相似已有知识（>=0.75）")
    similar_candidates: List[SimilarKnowledgeCandidate] = Field(default_factory=list, description="相似知识候选列表")


class InflowConfirmRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="关联的搜索会话ID")
    action: InflowAction = Field(default=InflowAction.CREATE_NEW, description="入库动作：创建新知识或更新已有知识")
    target_knowledge_id: Optional[str] = Field(default=None, description="当 action 为 update_existing 时的目标知识ID")
    title: str = Field(..., min_length=1, max_length=255, description="用户确认的知识标题")
    summary: Optional[str] = Field(default=None, description="用户确认的摘要")
    blocks: List[BlockItem] = Field(default_factory=list, description="用户编辑调整后的内容块")
    category_id: Optional[str] = Field(default=None, description="归属分类ID")
    tag_ids: Optional[List[str]] = Field(default_factory=list, description="关联标签ID列表")
    sources: Optional[List[InflowSourceItem]] = Field(default_factory=list, description="溯源引用列表")
    status: str = Field(default="published", description="知识状态（published 或 draft）")
