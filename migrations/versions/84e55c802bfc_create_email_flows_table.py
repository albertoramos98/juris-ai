"""create email_flows table

Revision ID: 84e55c802bfc
Revises: 17f7bc186e29
Create Date: 2026-02-02 18:17:24.517523

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84e55c802bfc'
down_revision: Union[str, Sequence[str], None] = '17f7bc186e29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        "email_flows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("office_id", sa.Integer(), sa.ForeignKey("offices.id"), nullable=False),
        sa.Column("process_id", sa.Integer(), sa.ForeignKey("processes.id"), nullable=False),

        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default=sa.text("10")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_sent_at", sa.DateTime(), nullable=True),

        sa.Column("template", sa.String(), nullable=False, server_default=sa.text("'cobranca_docs'")),
        sa.Column("stop_on_any_upload", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("stopped_reason", sa.String(), nullable=True),
        sa.Column("stopped_at", sa.DateTime(), nullable=True),

        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_index("ix_email_flows_office_id", "email_flows", ["office_id"])
    op.create_index("ix_email_flows_process_id", "email_flows", ["process_id"])


def downgrade() -> None:
    op.drop_index("ix_email_flows_process_id", table_name="email_flows")
    op.drop_index("ix_email_flows_office_id", table_name="email_flows")
    op.drop_table("email_flows")
