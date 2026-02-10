"""SQLAlchemy-based schema management."""

import logging

from sqlalchemy.engine import Engine

from nwtrack.infra.sqlite.orm_models import Base

logger = logging.getLogger(__name__)


class SQLAlchemySchemaManager:
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
