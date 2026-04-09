"""add is_active to users

Revision ID: 4b33e5f7fbd4
Revises: 84e55c802bfc
Create Date: 2026-02-05 16:27:09.169280
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4b33e5f7fbd4"
down_revision: Union[str, Sequence[str], None] = "84e55c802bfc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("users")]

    # Se a coluna já foi criada (por causa do erro no meio), não tenta criar de novo
    if "is_active" not in cols:
        op.add_column(
            "users",
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),  # no SQLite vira 1
            ),
        )

    # NÃO fazer op.alter_column(... drop default) no SQLite (quebra)


def downgrade() -> None:
    # No SQLite, drop column funciona via batch (copia tabela)
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("is_active")
