"""account display order and hidden flag

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-04

Adds ``accounts.display_order`` (1-based slot, backfilled from id rank) and
``accounts.is_hidden`` (default false).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

# batch mode reflects the live table to recreate it; the status CHECK may be
# unnamed on older databases, so it is passed explicitly or it would be dropped.
_TABLE_ARGS = (
    sa.CheckConstraint("status IN ('active', 'inactive')", name="check_account_status"),
)


def upgrade() -> None:
    with op.batch_alter_table("accounts", schema=None, table_args=_TABLE_ARGS) as b:
        b.add_column(
            sa.Column(
                "display_order", sa.Integer(), nullable=False, server_default="0"
            )
        )
        b.add_column(
            sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default="0")
        )

    op.execute(
        "UPDATE accounts SET display_order = "
        "(SELECT COUNT(*) FROM accounts a2 WHERE a2.id <= accounts.id)"
    )


def downgrade() -> None:
    with op.batch_alter_table("accounts", schema=None, table_args=_TABLE_ARGS) as b:
        b.drop_column("is_hidden")
        b.drop_column("display_order")
