"""
Application-wide logging configuration.
Must be called exactly once at startup.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

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


def setup_logging(app_name: str = "nwtrack") -> None:
    # ---- env ----
    log_dir = os.getenv("NWTRACK_LOG_DIR", "./logs/")
    file_level = _level(os.getenv("NWTRACK_LOG_FILE_LEVEL"), logging.INFO)
    console_level = _level(os.getenv("NWTRACK_LOG_CONSOLE_LEVEL"), logging.WARNING)
    rotation_bytes = int(os.getenv("NWTRACK_LOG_ROTATION_BYTES", 10 * 1024 * 1024))
    backup_count = int(os.getenv("NWTRACK_LOG_BACKUP_COUNT", 7))

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / f"{app_name}.log"

    # ---- app root logger ----
    app_logger = logging.getLogger(app_name)
    app_logger.setLevel(logging.DEBUG)  # handlers decide
    app_logger.propagate = False  # prevent double logs

    # Idempotency (important!)
    app_logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s|%(levelname)s|%(name)s|%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ---- console ----
    console = logging.StreamHandler()
    console.setLevel(console_level)
    console.setFormatter(formatter)

    # ---- rotating file ----
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=rotation_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)

    app_logger.addHandler(console)
    app_logger.addHandler(file_handler)
