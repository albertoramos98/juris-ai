"""add email_logs

Revision ID: c5c3f753593c
Revises: 0547ee1435c3
Create Date: 2026-01-28 16:49:51.205806

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5c3f753593c'
down_revision: Union[str, Sequence[str], None] = '0547ee1435c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
