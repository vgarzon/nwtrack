"""
Admin Serviced to manage initialization and setup
"""

from typing import Protocol

from nwtrack.config import Config
from nwtrack.dbmanager import DBConnectionManager


class DBAdminService(Protocol):
    """Admin services to manage initialization and setup."""

    def init_database(self) -> None:
        """Initialize the database schema."""
        ...


class SQLiteAdminService:
    """Admin services to manage initialization and setup."""

    def __init__(self, config: Config, db_conn: DBConnectionManager) -> None:
        self._config = config
        self._db_conn = db_conn

    def init_database(self) -> None:
        """Initialize the database schema."""
        print("Admin Service: Initializing database.")
        ddl_path = self._config.db_ddl_path
        with open(ddl_path, "r", encoding="utf-8") as f:
            ddl_script = f.read()
        self._db_conn.script(ddl_script)
