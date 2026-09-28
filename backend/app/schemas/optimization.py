from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.block import BlockItem


class OptimizationMode(str, Enum):
    CONCISE = "concise"              # 简洁易懂（MVP 默认：修正语病标点，理顺结构，删除冗余）
    STRUCTURED = "structured"        # 结构化整理（强化层级与大纲）
    FORMAL = "formal"                # 专业规范（规范专业术语表述）
    CORRECT_ONLY = "correct_only"    # 仅纠错（仅修改拼写标点，不改动词句）


class OptimizationRequest(BaseModel):
    content_markdown: Optional[str] = Field(default=None, description="待优化的 Markdown 格式文本")
    blocks: Optional[List[BlockItem]] = Field(default=None, description="待优化的编辑器内容块列表")
    mode: OptimizationMode = Field(default=OptimizationMode.CONCISE, description="AI 优化模式")


class OptimizationResponse(BaseModel):
    original_text: str = Field(description="优化前文本")
    polished_text: str = Field(description="优化后 Markdown 文本")
    blocks: List[BlockItem] = Field(default_factory=list, description="优化后的结构化内容块列表")
    changes_summary: str = Field(description="修改变更要点说明")
    suggested_category_id: Optional[str] = Field(default=None, description="智能推荐分类ID")
    suggested_category_name: Optional[str] = Field(default=None, description="智能推荐分类名称")
    suggested_tag_ids: List[str] = Field(default_factory=list, description="智能推荐标签ID列表")
    suggested_tag_names: List[str] = Field(default_factory=list, description="智能推荐标签名称列表")
