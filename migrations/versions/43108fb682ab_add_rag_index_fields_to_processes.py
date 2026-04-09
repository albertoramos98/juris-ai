"""add rag index fields to processes

Revision ID: 43108fb682ab
Revises: afad5bc38364
Create Date: 2026-02-23 15:49:31.853588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43108fb682ab'
down_revision: Union[str, Sequence[str], None] = 'afad5bc38364'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
   from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column("processes", sa.Column("rag_indexed_at", sa.DateTime(), nullable=True))
    op.add_column("processes", sa.Column("rag_chunk_count", sa.Integer(), nullable=False, server_default="0"))

def downgrade():
    op.drop_column("processes", "rag_chunk_count")
    op.drop_column("processes", "rag_indexed_at")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
