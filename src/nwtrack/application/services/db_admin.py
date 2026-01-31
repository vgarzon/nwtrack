"""
Database admin service to manage initialization and setup
"""

import logging

from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.infra.config.settings import Settings

logger = logging.getLogger(__name__)


class DBAdminService:
    """Database initialization and maintenance tasks."""

    def __init__(self, config: Settings, db: DBConnectionManager) -> None:
        self._config = config
        self._db = db

    def init_database(self) -> None:
        """Initialize the database schema."""
        logger.info(
            "Initializing database with DDL script '%s'", self._config.db_ddl_path
        )
        ddl_path = self._config.db_ddl_path
        with open(ddl_path, encoding="utf-8") as f:
            ddl_script = f.read()
        self._db.script(ddl_script)
