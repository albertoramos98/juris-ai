"""email flows

Revision ID: ff26d4560768
Revises: c5c3f753593c
Create Date: 2026-01-29 18:30:26.452431
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "ff26d4560768"
down_revision: Union[str, Sequence[str], None] = "c5c3f753593c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_flows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("office_id", sa.Integer(), sa.ForeignKey("offices.id"), nullable=False),
        sa.Column("process_id", sa.Integer(), sa.ForeignKey("processes.id"), nullable=False),

        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_sent_at", sa.DateTime(), nullable=True),

        sa.Column("template", sa.String(), nullable=False, server_default="cobranca_docs"),
        sa.Column("stop_on_any_upload", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("stopped_reason", sa.String(), nullable=True),
        sa.Column("stopped_at", sa.DateTime(), nullable=True),

        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_index("ix_email_flows_office_id", "email_flows", ["office_id"])
    op.create_index("ix_email_flows_process_id", "email_flows", ["process_id"])


def downgrade() -> None:
    op.drop_index("ix_email_flows_process_id", table_name="email_flows")
    op.drop_index("ix_email_flows_office_id", table_name="email_flows")
    op.drop_table("email_flows")
