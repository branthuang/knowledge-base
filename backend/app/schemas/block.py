import uuid
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class BlockType(str, Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    LIST = "list"
    TODO = "todo"
    QUOTE = "quote"
    CALLOUT = "callout"
    CODE = "code"
    TABLE = "table"
    IMAGE = "image"
    ATTACHMENT = "attachment"
    DIVIDER = "divider"


class BlockProperties(BaseModel):
    # Heading level (1-4)
    level: Optional[int] = Field(default=None, ge=1, le=4)
    # List style (bullet, ordered)
    list_style: Optional[str] = Field(default=None)
    # Todo check status
    checked: Optional[bool] = Field(default=None)
    # Callout tone/flavor (info, warning, error, success)
    callout_tone: Optional[str] = Field(default=None)
    # Code language
    language: Optional[str] = Field(default=None)
    # Image or attachment meta
    caption: Optional[str] = Field(default=None)
    width: Optional[int] = Field(default=None)
    file_name: Optional[str] = Field(default=None)
    file_size: Optional[int] = Field(default=None)
    mime_type: Optional[str] = Field(default=None)
    # Custom/extensible properties
    extra: Dict[str, Any] = Field(default_factory=dict)


class BlockItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: BlockType = Field(default=BlockType.PARAGRAPH)
    content: Union[str, List[Any], Dict[str, Any]] = Field(default="")
    properties: BlockProperties = Field(default_factory=BlockProperties)
    children: List["BlockItem"] = Field(default_factory=list)


# Support recursive block tree definition
BlockItem.model_rebuild()


class BlocksPayload(BaseModel):
    blocks: List[BlockItem] = Field(default_factory=list)
