"""
Database admin service to manage initialization and setup
"""

import logging

from nwtrack.application.ports.schema import SchemaManager
from nwtrack.infra.config.settings import Settings

logger = logging.getLogger(__name__)


class DBAdminService:
    """Database initialization and maintenance tasks."""

    def __init__(self, config: Settings, schema_manager: SchemaManager) -> None:
        """Initialize service with configuration and schema manager.

        Args:
            config: Application settings
            schema_manager: Schema management protocol implementation
        """
        self._config = config
        self._schema_manager = schema_manager

    def init_database(self) -> None:
        """Initialize the database schema.

        Drops all existing tables and recreates them from scratch.
        """
        logger.info(
            "Initializing database schema at '%s'",
            self._config.db_file_path,
        )
        self._schema_manager.drop_all_tables()
        self._schema_manager.create_all_tables()
