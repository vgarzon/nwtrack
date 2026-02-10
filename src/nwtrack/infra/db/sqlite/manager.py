"""
SQLite-specific session management.

This module contains SQLite dialect-specific code (PRAGMA commands, connection
parameters, etc.). The session manager can be replaced with PostgreSQL/MySQL
equivalents without affecting the ORM layer.
"""

import logging

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from nwtrack.infra.config.settings import Settings

logger = logging.getLogger(__name__)


class SQLiteSessionManager:
    """Manages SQLAlchemy engine and session factory for SQLite database."""

    def __init__(self, config: Settings):
        """Initialize session manager with configuration.

        Args:
            config: Application settings with database configuration
        """
        db_path = config.db_file_path
        url = f"sqlite:///{db_path}" if db_path != ":memory:" else "sqlite://"

        logger.info("Creating SQLAlchemy engine with URL: %s", url)

        # SQLite-specific: check_same_thread=False allows multi-threaded access
        self.engine: Engine = create_engine(
            url,
            echo=False,  # Set True for SQL logging during development
            connect_args={"check_same_thread": False},
        )

        # SQLite-specific: Enable foreign keys via PRAGMA
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        # Configure session factory
        # expire_on_commit=False allows entities to be used after session closes
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

    def create_session(self) -> Session:
        """Create a new Session instance.

        Returns:
            A new SQLAlchemy Session
        """
        return self.session_factory()
