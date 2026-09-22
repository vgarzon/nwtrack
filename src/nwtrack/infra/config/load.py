"""
Load configuration settings from config.toml, with environment variable overrides.
"""

import logging
import os
import tomllib
from pathlib import Path
from typing import Any

from nwtrack.application.dto import (
    ConfigFieldInfo,
    ConfigPathInfo,
    ConfigShowResult,
    ConfigValueSource,
)
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

_ENV_VARS: dict[str, str] = {
    "db_file_path": "NWTRACK_DATABASE__DB_FILE_PATH",
    "log_file": "NWTRACK_LOGGING__LOG_FILE",
    "log_file_level": "NWTRACK_LOGGING__LOG_FILE_LEVEL",
    "log_rotation_mb": "NWTRACK_LOGGING__LOG_ROTATION_MB",
    "log_backup_count": "NWTRACK_LOGGING__LOG_BACKUP_COUNT",
}


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


def _path_is_set(section: dict[str, Any], key: str) -> bool:
    """True if key is present with a non-empty string value (an explicit override)."""
    return key in section and section[key] != ""


def _path_value(
    section: dict[str, Any], key: str, default: str, table_name: str
) -> str:
    """Like `_str_value`, but an empty string ("") is treated as unset (use default)."""
    if not _path_is_set(section, key):
        return default
    return _str_value(section, key, default, table_name)


def _resolve() -> tuple[Settings, dict[str, ConfigValueSource]]:
    """Resolve Settings from config.toml + env overrides, tracking each source."""
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

    sources: dict[str, ConfigValueSource] = {
        "db_file_path": (
            ConfigValueSource.FILE
            if _path_is_set(database, "db_file_path")
            else ConfigValueSource.DEFAULT
        ),
        "log_file": (
            ConfigValueSource.FILE
            if _path_is_set(logging_section, "log_file")
            else ConfigValueSource.DEFAULT
        ),
        "log_file_level": (
            ConfigValueSource.FILE
            if "log_file_level" in logging_section
            else ConfigValueSource.DEFAULT
        ),
        "log_rotation_mb": (
            ConfigValueSource.FILE
            if "log_rotation_mb" in logging_section
            else ConfigValueSource.DEFAULT
        ),
        "log_backup_count": (
            ConfigValueSource.FILE
            if "log_backup_count" in logging_section
            else ConfigValueSource.DEFAULT
        ),
    }

    db_file_path = _path_value(
        database, "db_file_path", str(default_db_file_path()), "database"
    )
    log_file = _path_value(
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

    for field_name, env_var in _ENV_VARS.items():
        if field_name in ("db_file_path", "log_file"):
            continue
        if env_var in os.environ:
            sources[field_name] = ConfigValueSource.ENV

    if os.environ.get("NWTRACK_DATABASE__DB_FILE_PATH", "") != "":
        db_file_path = os.environ["NWTRACK_DATABASE__DB_FILE_PATH"]
        sources["db_file_path"] = ConfigValueSource.ENV
    if os.environ.get("NWTRACK_LOGGING__LOG_FILE", "") != "":
        log_file = os.environ["NWTRACK_LOGGING__LOG_FILE"]
        sources["log_file"] = ConfigValueSource.ENV
    if "NWTRACK_LOGGING__LOG_FILE_LEVEL" in os.environ:
        log_file_level = os.environ["NWTRACK_LOGGING__LOG_FILE_LEVEL"]
    if "NWTRACK_LOGGING__LOG_ROTATION_MB" in os.environ:
        log_rotation_mb = int(os.environ["NWTRACK_LOGGING__LOG_ROTATION_MB"])
    if "NWTRACK_LOGGING__LOG_BACKUP_COUNT" in os.environ:
        log_backup_count = int(os.environ["NWTRACK_LOGGING__LOG_BACKUP_COUNT"])

    if db_file_path != ":memory:":
        db_file_path = _resolve_path(db_file_path)
    log_file = _resolve_path(log_file)

    settings = Settings(
        db_file_path=db_file_path,
        log_file=log_file,
        log_file_level=log_file_level,
        log_rotation_mb=log_rotation_mb,
        log_backup_count=log_backup_count,
    )
    return settings, sources


def load_settings() -> Settings:
    """
    Load settings from config.toml (if found), with environment variable overrides.

    Returns:
        Settings: An instance of the Settings dataclass with resolved configuration.
    """
    settings, _sources = _resolve()
    return settings


def describe_settings() -> ConfigShowResult:
    """
    Describe the resolved configuration for display: search-path status and the
    effective value + source of every setting.

    Returns:
        ConfigShowResult: search paths (with existence/active flags) and resolved
        settings (with their source: env, file, or default).
    """
    settings, sources = _resolve()
    active = resolve_config_file()

    search_paths = [
        ConfigPathInfo(path=p, exists=p.is_file(), is_active=(p == active))
        for p in config_search_paths()
    ]
    fields = [
        ConfigFieldInfo(
            name="db_file_path",
            value=settings.db_file_path,
            source=sources["db_file_path"],
        ),
        ConfigFieldInfo(
            name="log_file", value=settings.log_file, source=sources["log_file"]
        ),
        ConfigFieldInfo(
            name="log_file_level",
            value=settings.log_file_level,
            source=sources["log_file_level"],
        ),
        ConfigFieldInfo(
            name="log_rotation_mb",
            value=str(settings.log_rotation_mb),
            source=sources["log_rotation_mb"],
        ),
        ConfigFieldInfo(
            name="log_backup_count",
            value=str(settings.log_backup_count),
            source=sources["log_backup_count"],
        ),
    ]
    return ConfigShowResult(search_paths=search_paths, fields=fields)
