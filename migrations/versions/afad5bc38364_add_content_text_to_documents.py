"""add content_text to documents

Revision ID: afad5bc38364
Revises: c9b1619d6083
Create Date: 2026-02-10 16:19:13.382482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'afad5bc38364'
down_revision: Union[str, Sequence[str], None] = 'c9b1619d6083'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "documents",
        sa.Column("content_text", sa.Text(), nullable=True),
    )

def downgrade():
    op.drop_column("documents", "content_text")

