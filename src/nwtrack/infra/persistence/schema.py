"""SQLAlchemy-based schema management."""

import logging

from alembic import command
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.engine import Engine, Inspector

from nwtrack.application.dto import SeedStatusHistoryResult
from nwtrack.infra.persistence.alembic_runtime import build_alembic_config
from nwtrack.infra.persistence.backup import backup_before_migration
from nwtrack.infra.persistence.orm.base import Base

logger = logging.getLogger(__name__)

_PRE_INSTITUTION_ID_REVISION = "0001"
_PRE_DISPLAY_ORDER_REVISION = "0002"


def _detect_stamp_revision(inspector: Inspector) -> str | None:
    """Classify an untracked database so it can be stamped before upgrading.

    Returns ``None`` when there is nothing to stamp (no ``accounts`` table at
    all — a brand new database that should run the full migration chain from
    scratch), the pre-institution_id baseline revision id for a legacy
    database missing that column, the pre-display-order revision id for a
    database with ``institution_id`` but no ``display_order``, or ``"head"``
    for a database that already has the full current schema but was never
    stamped.
    """
    if not inspector.has_table("accounts"):
        return None
    account_columns = {column["name"] for column in inspector.get_columns("accounts")}
    if "institution_id" not in account_columns:
        return _PRE_INSTITUTION_ID_REVISION
    if "display_order" not in account_columns:
        return _PRE_DISPLAY_ORDER_REVISION
    return "head"


class SchemaManager:
    """SQLAlchemy implementation of SchemaManager protocol."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def drop_all_tables(self) -> None:
        """Drop all tables (destructive operation)."""
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(self._engine)

    def create_all_tables(self) -> None:
        """Create all tables from ORM definitions and stamp them at head."""
        logger.info("Creating tables from ORM models...")
        Base.metadata.create_all(self._engine)
        with self._engine.connect() as connection:
            command.stamp(build_alembic_config(connection), "head")
            connection.commit()

    def ensure_current_schema(self) -> None:
        """Bring the database to the current schema via Alembic migrations.

        Adopts an untracked database (one with no ``alembic_version`` table)
        by stamping it at the revision matching its actual shape, then runs
        any pending migrations. A pre-migration backup of the database file
        is taken whenever a real schema change is about to be applied.
        """
        logger.info("Ensuring current database schema...")
        with self._engine.connect() as connection:
            config = build_alembic_config(connection)
            inspector = inspect(connection)
            had_existing_tables = bool(inspector.get_table_names())

            if not inspector.has_table("alembic_version"):
                stamp_revision = _detect_stamp_revision(inspector)
                if stamp_revision is not None:
                    command.stamp(config, stamp_revision)
                    connection.commit()

            head_revision = ScriptDirectory.from_config(config).get_current_head()
            current_revision = MigrationContext.configure(
                connection
            ).get_current_revision()

            if current_revision == head_revision:
                return

        # Nothing existed before (a brand new database) — there is no data to
        # protect, so skip the no-op backup and let `upgrade head` create the
        # full schema from scratch.
        backup_path = (
            backup_before_migration(self._engine) if had_existing_tables else None
        )
        try:
            with self._engine.connect() as connection:
                command.upgrade(build_alembic_config(connection), "head")
                connection.commit()
        except Exception as exc:
            message = "Database schema migration failed."
            if backup_path is not None:
                message += (
                    f" A pre-migration backup was saved to '{backup_path}'; "
                    "restore it if the database is now in an unexpected state."
                )
            raise RuntimeError(message) from exc

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
