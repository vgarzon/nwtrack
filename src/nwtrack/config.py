"""
Load and manage configuration settings.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    db_file_path: str


def _load() -> Settings:
    """
    Load settings from environment variables or use default values.

    Returns:
        Settings: An instance of the Settings dataclass with loaded configuration.
    """
    db_file_path = os.getenv("DB_FILE_PATH", ":memory:")
    return Settings(db_file_path=db_file_path)


settings = _load()
