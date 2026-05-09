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
