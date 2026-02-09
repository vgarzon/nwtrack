"""
SQLAlchemy engine and session management.
"""

import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from nwtrack.infra.config.settings import Settings

logger = logging.getLogger(__name__)


class SQLAlchemySessionManager:
    """Manages SQLAlchemy engine and session factory."""

    def __init__(self, config: Settings):
        """Initialize session manager with configuration.

        Args:
            config: Application settings with database configuration
        """
        db_path = config.db_file_path
        url = f"sqlite:///{db_path}" if db_path != ":memory:" else "sqlite://"

        logger.info("Creating SQLAlchemy engine with URL: %s", url)

        self.engine: Engine = create_engine(
            url,
            echo=False,  # Set True for SQL logging during development
            connect_args={"check_same_thread": False},
        )

        # Enable foreign keys for SQLite
        from sqlalchemy import event

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        self.session_factory = sessionmaker(bind=self.engine)

    def create_session(self) -> Session:
        """Create a new Session instance.

        Returns:
            A new SQLAlchemy Session
        """
        return self.session_factory()
