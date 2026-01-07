"""
Database admin service to manage initialization and setup
"""

from nwtrack.infra.config.settings import Settings
from nwtrack.application.ports.db import DBConnectionManager


class DBAdminService:
    """Database initialization and maintenance tasks."""

    def __init__(self, config: Settings, db: DBConnectionManager) -> None:
        self._config = config
        self._db = db

    def init_database(self) -> None:
        """Initialize the database schema."""
        print(f"Initializing database using DDL script at {self._config.db_ddl_path}")
        ddl_path = self._config.db_ddl_path
        with open(ddl_path, "r", encoding="utf-8") as f:
            ddl_script = f.read()
        self._db.script(ddl_script)
