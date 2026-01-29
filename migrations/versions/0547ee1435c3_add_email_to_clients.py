"""add email to clients

Revision ID: 0547ee1435c3
Revises: 799ce7344c24
Create Date: 2026-01-28 16:38:38.461920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0547ee1435c3'
down_revision: Union[str, Sequence[str], None] = '799ce7344c24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    op.add_column("clients", sa.Column("email", sa.String(), nullable=True))

def downgrade():
    op.drop_column("clients", "email")
