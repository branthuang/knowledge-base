"""Initial database schema with pgvector

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-28 12:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Table: categories
    op.create_table(
        "categories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("color", sa.String(30), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_categories_name", "categories", ["name"])
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])

    # 3. Table: tags
    op.create_table(
        "tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("tags.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tags_name", "tags", ["name"])
    op.create_index("ix_tags_parent_id", "tags", ["parent_id"])

    # 4. Table: knowledge_items
    op.create_table(
        "knowledge_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("blocks_json", sa.JSON(), nullable=False),
        sa.Column("plain_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("category_id", sa.String(36), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_type", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("favorite", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("index_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_knowledge_items_title", "knowledge_items", ["title"])
    op.create_index("ix_knowledge_items_category_id", "knowledge_items", ["category_id"])
    op.create_index("ix_knowledge_items_source_type", "knowledge_items", ["source_type"])
    op.create_index("ix_knowledge_items_status", "knowledge_items", ["status"])
    op.create_index("ix_knowledge_items_favorite", "knowledge_items", ["favorite"])
    op.create_index("ix_knowledge_items_index_status", "knowledge_items", ["index_status"])

    # 5. Table: knowledge_tags
    op.create_table(
        "knowledge_tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("knowledge_id", sa.String(36), sa.ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag_id", sa.String(36), sa.ForeignKey("tags.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("knowledge_id", "tag_id", name="uq_knowledge_tag"),
    )
    op.create_index("ix_knowledge_tags_knowledge_id", "knowledge_tags", ["knowledge_id"])
    op.create_index("ix_knowledge_tags_tag_id", "knowledge_tags", ["tag_id"])

    # 6. Table: knowledge_sources
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("knowledge_id", sa.String(36), sa.ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_knowledge_sources_knowledge_id", "knowledge_sources", ["knowledge_id"])

    # 7. Table: search_sessions
    op.create_table(
        "search_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(30), nullable=False, server_default="knowledge_first"),
        sa.Column("local_hits_json", sa.JSON(), nullable=False),
        sa.Column("ai_answer", sa.Text(), nullable=True),
        sa.Column("citations_json", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("model", sa.String(50), nullable=True),
        sa.Column("saved_knowledge_id", sa.String(36), sa.ForeignKey("knowledge_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_search_sessions_saved_knowledge_id", "search_sessions", ["saved_knowledge_id"])

    # 8. Table: embedding_chunks
    op.create_table(
        "embedding_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("knowledge_id", sa.String(36), sa.ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("block_id", sa.String(36), nullable=True),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_embedding_chunks_knowledge_id", "embedding_chunks", ["knowledge_id"])
    op.create_index("ix_embedding_chunks_block_id", "embedding_chunks", ["block_id"])

    # 9. Table: assets
    op.create_table(
        "assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("storage_key", sa.String(255), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("hash", sa.String(64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_assets_storage_key", "assets", ["storage_key"])
    op.create_index("ix_assets_hash", "assets", ["hash"])


def downgrade() -> None:
    op.drop_table("assets")
    op.drop_table("embedding_chunks")
    op.drop_table("search_sessions")
    op.drop_table("knowledge_sources")
    op.drop_table("knowledge_tags")
    op.drop_table("knowledge_items")
    op.drop_table("tags")
    op.drop_table("categories")
    op.execute("DROP EXTENSION IF EXISTS vector;")
