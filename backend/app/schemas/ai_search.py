from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SearchMode(str, Enum):
    KNOWLEDGE_FIRST = "knowledge_first"          # 知识优先（默认）：本地优先，充分时仅用本地知识，不足时公网补充
    EXTERNAL_SUPPLEMENT = "external_supplement"  # 强制本地与外部公网补充综合回答
    KNOWLEDGE_ONLY = "knowledge_only"            # 严格仅查本地知识库，绝不发起外部请求
    DIRECT_AI = "direct_ai"                      # 直接向 AI 提问（侧边附带本地关联）


class CitationItem(BaseModel):
    title: str = Field(description="来源标题")
    url: str = Field(description="来源完整链接")
    snippet: str = Field(description="引用文本摘要")
    source_name: Optional[str] = Field(default=None, description="来源站点或域名")
    published_at: Optional[str] = Field(default=None, description="发布或抓取时间")


class LocalHitRef(BaseModel):
    id: str = Field(description="知识点ID")
    title: str = Field(description="知识点标题")
    snippet: str = Field(description="命中分块片段")
    score: float = Field(description="综合匹配得分")
    category_name: Optional[str] = Field(default=None, description="分类名称")


class AISearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="用户搜索或提问内容")
    mode: SearchMode = Field(default=SearchMode.KNOWLEDGE_FIRST, description="搜索与问答模式")
    session_id: Optional[str] = Field(default=None, description="会话ID（若为空则自动创建）")
    category_id: Optional[str] = Field(default=None, description="分类过滤约束")
    tag_ids: Optional[List[str]] = Field(default=None, description="标签过滤约束")
    minimum_score: float = Field(default=0.60, ge=0.0, le=1.0, description="本地知识充分性判定阈值")


class AISearchResponse(BaseModel):
    session_id: str = Field(description="搜索会话ID")
    query: str = Field(description="用户问题")
    mode: SearchMode = Field(description="执行模式")
    ai_answer: str = Field(description="AI 综合组织回答")
    is_sufficient: bool = Field(description="本地知识是否充足")
    local_hits: List[LocalHitRef] = Field(default_factory=list, description="引用的本地知识列表")
    citations: List[CitationItem] = Field(default_factory=list, description="引用的公网或外部链接")
    model_used: str = Field(description="生成回答调用的模型")
    created_at: datetime = Field(description="会话创建时间")


class SearchSessionListItem(BaseModel):
    id: str = Field(description="会话ID")
    query: str = Field(description="用户查询")
    mode: str = Field(description="搜索模式")
    ai_answer_preview: Optional[str] = Field(default=None, description="回答摘要预览")
    model: Optional[str] = Field(default=None, description="模型名称")
    saved_knowledge_id: Optional[str] = Field(default=None, description="已沉淀落库的知识点ID")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class SearchSessionDetailResponse(BaseModel):
    id: str = Field(description="会话ID")
    query: str = Field(description="用户查询")
    mode: str = Field(description="搜索模式")
    local_hits_json: List[Dict[str, Any]] = Field(default_factory=list, description="命中的本地知识快照")
    citations_json: List[Dict[str, Any]] = Field(default_factory=list, description="外部引用列表快照")
    ai_answer: Optional[str] = Field(default=None, description="AI 完整回答")
    provider: Optional[str] = Field(default=None, description="Provider 标识")
    model: Optional[str] = Field(default=None, description="模型名称")
    saved_knowledge_id: Optional[str] = Field(default=None, description="已沉淀落库的知识点ID")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(from_attributes=True)
