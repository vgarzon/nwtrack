"""
Load configuration settings from config.toml, with environment variable overrides.
"""

import logging
import os
import tomllib
from pathlib import Path
from typing import Any

from nwtrack.infra.config.paths import (
    config_search_paths,
    default_db_file_path,
    default_log_file_path,
    resolve_config_file,
)
from nwtrack.infra.config.settings import Settings

logger = logging.getLogger(__name__)

_DEFAULT_LOG_FILE_LEVEL = "INFO"
_DEFAULT_LOG_ROTATION_MB = 10
_DEFAULT_LOG_BACKUP_COUNT = 7


def _resolve_path(value: str) -> str:
    """Resolve a config.toml path value relative to the current working directory."""
    return str(Path(value).resolve())


def _load_toml(config_file: Path) -> dict[str, Any]:
    try:
        with config_file.open("rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(
            f"Failed to parse '{config_file}': invalid TOML syntax ({exc})."
        ) from exc


def _int_value(section: dict[str, Any], key: str, default: int, table_name: str) -> int:
    if key not in section:
        return default
    value = section[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"Config value '[{table_name}].{key}' must be an integer, got {value!r}."
        )
    return value


def _str_value(section: dict[str, Any], key: str, default: str, table_name: str) -> str:
    value = section.get(key, default)
    if not isinstance(value, str):
        raise ValueError(
            f"Config value '[{table_name}].{key}' must be a string, got {value!r}."
        )
    return value


def load_settings() -> Settings:
    """
    Load settings from config.toml (if found), with environment variable overrides.

    Returns:
        Settings: An instance of the Settings dataclass with resolved configuration.
    """
    config_file = resolve_config_file()

    database: dict[str, Any] = {}
    logging_section: dict[str, Any] = {}

    if config_file is not None:
        data = _load_toml(config_file)
        database = data.get("database", {})
        logging_section = data.get("logging", {})
    else:
        searched = ", ".join(str(p) for p in config_search_paths())
        logger.warning(
            "No config.toml found. Searched: %s. Using built-in defaults. "
            "Run 'nwtrack config init' to create one.",
            searched,
        )

    db_file_path = _str_value(
        database, "db_file_path", str(default_db_file_path()), "database"
    )
    log_file = _str_value(
        logging_section, "log_file", str(default_log_file_path()), "logging"
    )
    log_file_level = _str_value(
        logging_section, "log_file_level", _DEFAULT_LOG_FILE_LEVEL, "logging"
    )
    log_rotation_mb = _int_value(
        logging_section, "log_rotation_mb", _DEFAULT_LOG_ROTATION_MB, "logging"
    )
    log_backup_count = _int_value(
        logging_section, "log_backup_count", _DEFAULT_LOG_BACKUP_COUNT, "logging"
    )

    if "NWTRACK_DATABASE__DB_FILE_PATH" in os.environ:
        db_file_path = os.environ["NWTRACK_DATABASE__DB_FILE_PATH"]
    if "NWTRACK_LOGGING__LOG_FILE" in os.environ:
        log_file = os.environ["NWTRACK_LOGGING__LOG_FILE"]
    if "NWTRACK_LOGGING__LOG_FILE_LEVEL" in os.environ:
        log_file_level = os.environ["NWTRACK_LOGGING__LOG_FILE_LEVEL"]
    if "NWTRACK_LOGGING__LOG_ROTATION_MB" in os.environ:
        log_rotation_mb = int(os.environ["NWTRACK_LOGGING__LOG_ROTATION_MB"])
    if "NWTRACK_LOGGING__LOG_BACKUP_COUNT" in os.environ:
        log_backup_count = int(os.environ["NWTRACK_LOGGING__LOG_BACKUP_COUNT"])

    if db_file_path != ":memory:":
        db_file_path = _resolve_path(db_file_path)
    log_file = _resolve_path(log_file)

    return Settings(
        db_file_path=db_file_path,
        log_file=log_file,
        log_file_level=log_file_level,
        log_rotation_mb=log_rotation_mb,
        log_backup_count=log_backup_count,
    )
