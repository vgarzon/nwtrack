"""SQLAlchemy-based schema management."""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from nwtrack.infra.persistence.orm.base import Base

logger = logging.getLogger(__name__)


class SchemaManager:
    """SQLAlchemy implementation of SchemaManager protocol."""

    def __init__(self, engine: Engine) -> None:
        """Initialize with SQLAlchemy engine.

        Args:
            engine: SQLAlchemy Engine instance
        """
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
        self._seed_account_status_history()

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

    def _seed_account_status_history(self) -> None:
        """Seed one initial status-history row per account that lacks one.

        Uses the account's current status and its earliest balance month
        (or '1900-01' for accounts with no balance records).
        Safe to call repeatedly — INSERT OR IGNORE prevents duplicates.
        """
        inspector = inspect(self._engine)
        if not inspector.has_table("account_status_history"):
            logger.warning("account_status_history table missing; skipping seed.")
            return
        if not inspector.has_table("accounts"):
            return

        logger.info("Seeding account_status_history for accounts without history rows.")
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT OR IGNORE INTO account_status_history "
                    "  (account_id, status, effective_month) "
                    "SELECT a.id, a.status, COALESCE(MIN(b.month), '1900-01') "
                    "FROM accounts a "
                    "LEFT JOIN balances b ON b.account_id = a.id "
                    "WHERE a.id NOT IN "
                    "  (SELECT DISTINCT account_id FROM account_status_history) "
                    "GROUP BY a.id, a.status"
                )
            )
        logger.info("account_status_history seeding complete.")
