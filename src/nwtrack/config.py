"""
Load and manage configuration settings.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    db_file_path: str
    db_ddl_path: str


def load_config() -> Config:
    """
    Load settings from environment variables or use default values.

    Returns:
        Settings: An instance of the Settings dataclass with loaded configuration.
    """
    db_file_path = os.getenv("NWTRACK_DB_FILE_PATH", ":memory:")
    db_ddl_path = os.getenv("NWTRACK_DB_DDL_PATH", "sql/nwtrack_ddl.sql")
    return Config(db_file_path=db_file_path, db_ddl_path=db_ddl_path)
