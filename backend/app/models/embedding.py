import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.db.session import Base
from app.core.config import settings


class EmbeddingChunk(Base):
    __tablename__ = "embedding_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_id: Mapped[str] = mapped_column(String(36), ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False, index=True)
    block_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    knowledge_item: Mapped["KnowledgeItem"] = relationship("KnowledgeItem", back_populates="chunks")

    def __init__(self, **kwargs):
        kwargs.setdefault("id", str(uuid.uuid4()))
        kwargs.setdefault("token_count", 0)
        super().__init__(**kwargs)
