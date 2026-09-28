import uuid
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Text, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class SearchSession(Base):
    __tablename__ = "search_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(String(30), default="knowledge_first", nullable=False)  # knowledge_first, supplementary, knowledge_only, direct_ai
    local_hits_json: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    ai_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citations_json: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    saved_knowledge_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("knowledge_items.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    saved_knowledge: Mapped[Optional["KnowledgeItem"]] = relationship("KnowledgeItem")

    def __init__(self, **kwargs):
        kwargs.setdefault("id", str(uuid.uuid4()))
        kwargs.setdefault("mode", "knowledge_first")
        kwargs.setdefault("local_hits_json", [])
        kwargs.setdefault("citations_json", [])
        super().__init__(**kwargs)
