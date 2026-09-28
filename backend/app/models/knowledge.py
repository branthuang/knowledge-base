import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blocks_json: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)
    plain_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String(30), default="manual", nullable=False, index=True)  # manual, ai_search, import, web_clip
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)  # draft, published, archived, trashed
    favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    index_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)  # pending, indexed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="knowledge_items")
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary="knowledge_tags",
        back_populates="knowledge_items",
    )
    sources: Mapped[List["KnowledgeSource"]] = relationship("KnowledgeSource", back_populates="knowledge_item", cascade="all, delete-orphan")
    chunks: Mapped[List["EmbeddingChunk"]] = relationship("EmbeddingChunk", back_populates="knowledge_item", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        kwargs.setdefault("id", str(uuid.uuid4()))
        kwargs.setdefault("source_type", "manual")
        kwargs.setdefault("status", "draft")
        kwargs.setdefault("favorite", False)
        kwargs.setdefault("index_status", "pending")
        kwargs.setdefault("blocks_json", [])
        kwargs.setdefault("plain_text", "")
        super().__init__(**kwargs)
