"""SQLAlchemy-based schema management."""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from nwtrack.application.dto import SeedStatusHistoryResult
from nwtrack.infra.persistence.orm.base import Base

logger = logging.getLogger(__name__)


class SchemaManager:
    """SQLAlchemy implementation of SchemaManager protocol."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def drop_all_tables(self) -> None:
        """Drop all tables (destructive operation)."""
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(self._engine)

    def create_all_tables(self) -> None:
        """Create all tables from ORM definitions."""
        logger.info("Creating tables from ORM models...")
        Base.metadata.create_all(self._engine)

    def ensure_current_schema(self) -> None:
        """Create missing tables and apply supported compatibility upgrades."""
        logger.info("Ensuring current database schema...")
        Base.metadata.create_all(self._engine)
        self._ensure_sqlite_legacy_columns()

    def _ensure_sqlite_legacy_columns(self) -> None:
        """Apply the supported SQLite compatibility upgrades in place."""
        if self._engine.dialect.name != "sqlite":
            return

        inspector = inspect(self._engine)
        if not inspector.has_table("accounts"):
            return

        account_columns = {
            column["name"] for column in inspector.get_columns("accounts")
        }
        if "institution_id" in account_columns:
            return

        logger.info("Adding missing nullable accounts.institution_id column.")
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE accounts "
                    "ADD COLUMN institution_id INTEGER REFERENCES institutions(id)"
                )
            )

    def seed_account_status_history(self) -> SeedStatusHistoryResult:
        """Seed status-history rows based on balance history and current account status.

        For active accounts: one row (active, first_balance_month).
        For inactive accounts with distinct first/last balance months: two rows —
        (active, first_balance_month) and (inactive, last_balance_month).
        For inactive accounts with no balance history or a single balance month:
        one row (inactive, that_month or '1900-01').

        Also migrates old-style seeded rows: a single (inactive, first_month) row
        for an account with a distinct last balance month is replaced with the
        two-row form above.

        Accounts that already have two or more history rows are left unchanged.
        Safe to call repeatedly.

        Returns:
            SeedStatusHistoryResult with seeded, migrated, and skipped counts.
        """
        inspector = inspect(self._engine)
        if not inspector.has_table("account_status_history"):
            logger.warning("account_status_history table missing; skipping seed.")
            return SeedStatusHistoryResult(seeded=0, migrated=0, skipped=0)
        if not inspector.has_table("accounts"):
            return SeedStatusHistoryResult(seeded=0, migrated=0, skipped=0)

        from sqlalchemy import select
        from sqlalchemy.orm import Session

        from nwtrack.domain.value_objects import Month
        from nwtrack.infra.persistence.orm.models import (
            Account,
            AccountStatusHistory,
            Balance,
            Status,
        )

        sentinel = Month(1900, 1)
        seeded = 0
        migrated = 0
        skipped = 0

        logger.info("Seeding account_status_history...")
        with Session(self._engine) as session:
            accounts = session.execute(select(Account)).scalars().all()

            for account in accounts:
                existing = list(
                    session.execute(
                        select(AccountStatusHistory)
                        .where(AccountStatusHistory.account_id == account.id)
                        .order_by(AccountStatusHistory.effective_month)
                    ).scalars().all()
                )

                balance_months = list(
                    session.execute(
                        select(Balance.month)
                        .where(Balance.account_id == account.id)
                        .order_by(Balance.month)
                    ).scalars().all()
                )

                first_month: Month = balance_months[0] if balance_months else sentinel
                last_month: Month | None = (
                    balance_months[-1] if balance_months else None
                )

                if account.status == Status.ACTIVE:
                    if not existing:
                        session.add(AccountStatusHistory(
                            account_id=account.id,
                            status=Status.ACTIVE,
                            effective_month=first_month,
                        ))
                        seeded += 1
                    else:
                        skipped += 1
                else:
                    if not existing:
                        if last_month is not None and last_month != first_month:
                            session.add(AccountStatusHistory(
                                account_id=account.id,
                                status=Status.ACTIVE,
                                effective_month=first_month,
                            ))
                            session.add(AccountStatusHistory(
                                account_id=account.id,
                                status=account.status,
                                effective_month=last_month,
                            ))
                        else:
                            session.add(AccountStatusHistory(
                                account_id=account.id,
                                status=account.status,
                                effective_month=(
                                    last_month if last_month else first_month
                                ),
                            ))
                        seeded += 1
                    elif (
                        len(existing) == 1
                        and existing[0].status != Status.ACTIVE
                        and last_month is not None
                        and last_month != first_month
                    ):
                        # Migrate old-style seed: single non-active row → two rows
                        session.delete(existing[0])
                        session.flush()
                        session.add(AccountStatusHistory(
                            account_id=account.id,
                            status=Status.ACTIVE,
                            effective_month=first_month,
                        ))
                        session.add(AccountStatusHistory(
                            account_id=account.id,
                            status=account.status,
                            effective_month=last_month,
                        ))
                        migrated += 1
                    else:
                        skipped += 1

            session.commit()

        logger.info(
            "account_status_history seeding complete: "
            "%d seeded, %d migrated, %d skipped.",
            seeded, migrated, skipped,
        )
        return SeedStatusHistoryResult(
            seeded=seeded, migrated=migrated, skipped=skipped
        )
