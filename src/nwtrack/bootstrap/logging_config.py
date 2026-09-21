"""
Application-wide logging configuration.
Must be called exactly once at startup.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from nwtrack.infra.config.settings import Settings

_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def _level(name: str | None, default: int) -> int:
    if not name:
        return default
    return _LEVELS.get(name.upper(), default)


def setup_logging(settings: Settings) -> None:
    log_file = settings.log_file
    file_level = _level(settings.log_file_level, logging.INFO)
    rotation_bytes = settings.log_rotation_mb * 1024 * 1024
    backup_count = settings.log_backup_count

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # ---- app root logger ----
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Idempotency (important!)
    root_logger.handlers.clear()

    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ---- rotating file ----
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=rotation_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)

    root_logger.addHandler(file_handler)
