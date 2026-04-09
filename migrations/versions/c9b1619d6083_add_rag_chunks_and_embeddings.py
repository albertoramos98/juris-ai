"""add rag chunks and embeddings

Revision ID: c9b1619d6083
Revises: 4b33e5f7fbd4
Create Date: 2026-02-10 16:00:24.602626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9b1619d6083'
down_revision: Union[str, Sequence[str], None] = '4b33e5f7fbd4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("office_id", sa.Integer(), sa.ForeignKey("offices.id"), nullable=False),
        sa.Column("process_id", sa.Integer(), sa.ForeignKey("processes.id"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_document_chunks_office_id", "document_chunks", ["office_id"])
    op.create_index("ix_document_chunks_process_id", "document_chunks", ["process_id"])
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])

    op.create_table(
        "chunk_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("office_id", sa.Integer(), sa.ForeignKey("offices.id"), nullable=False),
        sa.Column("process_id", sa.Integer(), sa.ForeignKey("processes.id"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("chunk_id", sa.Integer(), sa.ForeignKey("document_chunks.id"), nullable=False),
        sa.Column("model", sa.String(), nullable=False, server_default="text-embedding-3-small"),
        sa.Column("embedding_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chunk_embeddings_office_id", "chunk_embeddings", ["office_id"])
    op.create_index("ix_chunk_embeddings_process_id", "chunk_embeddings", ["process_id"])
    op.create_index("ix_chunk_embeddings_document_id", "chunk_embeddings", ["document_id"])
    op.create_index("ix_chunk_embeddings_chunk_id", "chunk_embeddings", ["chunk_id"])


def downgrade() -> None:
    op.drop_table("chunk_embeddings")
    op.drop_table("document_chunks")
