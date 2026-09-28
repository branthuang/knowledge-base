from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="分类名称")
    parent_id: Optional[str] = Field(default=None, description="父分类 ID")
    description: Optional[str] = Field(default=None, description="分类说明")
    icon: Optional[str] = Field(default=None, max_length=50, description="图标标识")
    color: Optional[str] = Field(default=None, max_length=30, description="颜色标识")
    sort_order: int = Field(default=0, description="排序权重")
    status: str = Field(default="active", description="状态: active / inactive")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    parent_id: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    knowledge_count: int = 0


class CategoryTreeNode(CategoryResponse):
    model_config = ConfigDict(from_attributes=True)

    children: List["CategoryTreeNode"] = Field(default_factory=list)


CategoryTreeNode.model_rebuild()


class CategoryDeleteRequest(BaseModel):
    reassign_to_id: Optional[str] = Field(
        default=None,
        description="目标分类 ID，若指定为 'unclassified' 则重置为未分类；若为 None 且存在关联知识则阻断删除",
    )
