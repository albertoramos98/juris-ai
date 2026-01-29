"""add email_logs

Revision ID: 799ce7344c24
Revises: 51e38aaa538b
Create Date: 2026-01-28 16:32:34.454746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '799ce7344c24'
down_revision: Union[str, Sequence[str], None] = '51e38aaa538b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
