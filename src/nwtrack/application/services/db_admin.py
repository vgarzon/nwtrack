"""
Database admin service to manage initialization and setup
"""

import logging

from nwtrack.infra.config.settings import Settings
from nwtrack.infra.sqlite.orm_models import Base
from nwtrack.infra.sqlite.sqlalchemy_manager import SQLAlchemySessionManager

logger = logging.getLogger(__name__)


class DBAdminService:
    """Database initialization and maintenance tasks."""

    def __init__(
        self, config: Settings, session_manager: SQLAlchemySessionManager
    ) -> None:
        self._config = config
        self._session_manager = session_manager

    def init_database(self) -> None:
        """Initialize the database schema using SQLAlchemy metadata."""
        logger.info(
            "Initializing database schema at '%s' using SQLAlchemy",
            self._config.db_file_path
        )
        Base.metadata.create_all(self._session_manager.engine)
