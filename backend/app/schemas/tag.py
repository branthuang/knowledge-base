from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TagBase(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="标签名称")
    parent_id: Optional[str] = Field(default=None, description="父标签 ID")
    description: Optional[str] = Field(default=None, description="标签说明")
    color: Optional[str] = Field(default=None, max_length=30, description="颜色标识")


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    parent_id: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class TagResponse(TagBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class TagWithStatsResponse(TagResponse):
    model_config = ConfigDict(from_attributes=True)

    knowledge_count: int = 0
    last_used_at: Optional[datetime] = None


class TagMergeRequest(BaseModel):
    source_tag_id: str = Field(description="源标签 ID（合并后被安全删除）")
    target_tag_id: str = Field(description="目标标签 ID（合并后保留并继承所有知识关联）")
