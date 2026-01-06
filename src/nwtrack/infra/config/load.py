"""
Load configuration settings.
"""

import os

from dotenv import load_dotenv
from nwtrack.infra.config.settings import Settings

load_dotenv()


def load_settings() -> Settings:
    """
    Load settings from environment variables or use default values.

    Returns:
        Settings: An instance of the Settings dataclass with loaded configuration.
    """
    db_file_path = os.getenv("NWTRACK_DB_FILE_PATH", ":memory:")
    db_ddl_path = os.getenv("NWTRACK_DB_DDL_PATH", "sql/nwtrack_ddl.sql")
    return Settings(db_file_path=db_file_path, db_ddl_path=db_ddl_path)
