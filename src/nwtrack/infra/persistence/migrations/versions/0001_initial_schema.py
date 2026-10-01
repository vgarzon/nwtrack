"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-30

The oldest schema shape nwtrack has shipped: currencies, categories, and
accounts only (no institutions, tags, balances, status history, or exchange
rates yet, and accounts has no institution_id column). This mirrors the
"pre-Phase-10" fixture used in tests/services/test_db_admin_service.py and
exists so that an untracked pre-institution_id database can be stamped at
this revision before upgrading to head.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "currencies",
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "categories",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("side", sa.String(), nullable=False),
        sa.CheckConstraint(
            "side IN ('asset', 'liability')", name="check_category_side"
        ),
        sa.PrimaryKeyConstraint("name"),
    )
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'inactive')", name="check_account_status"
        ),
        sa.ForeignKeyConstraint(["category"], ["categories.name"]),
        sa.ForeignKeyConstraint(["currency"], ["currencies.code"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )


def downgrade() -> None:
    op.drop_table("accounts")
    op.drop_table("categories")
    op.drop_table("currencies")
