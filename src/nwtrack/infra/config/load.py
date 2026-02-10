"""
Load configuration settings.
"""

import logging
import os

from nwtrack.infra.config.settings import Settings

logger = logging.getLogger(__name__)


def load_settings() -> Settings:
    """
    Load settings from environment variables or use default values.

    Returns:
        Settings: An instance of the Settings dataclass with loaded configuration.
    """
    if "NWTRACK_DB_FILE_PATH" in os.environ:
        db_file_path = os.environ["NWTRACK_DB_FILE_PATH"]
    else:
        logger.warning(
            "Environment variable 'NWTRACK_DB_FILE_PATH' not set. "
            "Using default in-memory database."
        )
        db_file_path = ":memory:"

    return Settings(db_file_path=db_file_path)
