"""
Resolve standard per-OS locations for nwtrack's config, data, and log files.
"""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir, user_log_dir

_APP_NAME = "nwtrack"
_CONFIG_FILE_NAME = "config.toml"
_DB_FILE_NAME = "nwtrack.db"
_LOG_FILE_NAME = "nwtrack.log"


class ConfigFileOverrideSource(StrEnum):
    """How an explicit config file path was supplied."""

    FLAG = "--config-file"
    ENV = "NWTRACK_CONFIG_FILE"


@dataclass(frozen=True)
class ConfigFileOverride:
    """An explicit config file path that bypasses the search path."""

    path: Path
    source: ConfigFileOverrideSource


class ConfigFileNotFoundError(ValueError):
    """Raised when an explicit config file override names a missing file."""


_config_file_override: ConfigFileOverride | None = None


def set_config_file_override(override: ConfigFileOverride | None) -> None:
    """Record (or clear, with None) the process-wide explicit config file path."""
    global _config_file_override
    _config_file_override = override


def get_config_file_override() -> ConfigFileOverride | None:
    """Return the explicit config file path in effect, if any."""
    return _config_file_override


def default_config_dir() -> Path:
    """Standard per-OS config directory; lowest search priority and the default
    write target for `config init`."""
    return Path(user_config_dir(_APP_NAME))


def config_search_paths() -> list[Path]:
    """Candidate `config.toml` locations, in priority order (first found wins)."""
    return [
        Path("./config") / _APP_NAME / _CONFIG_FILE_NAME,
        Path.home() / ".config" / _APP_NAME / _CONFIG_FILE_NAME,
        default_config_dir() / _CONFIG_FILE_NAME,
    ]


def resolve_config_file() -> Path | None:
    """Return the config.toml in effect, or None.

    An explicit override (flag or env var) bypasses the search path and must exist;
    otherwise the first existing file on the search path is returned.
    """
    override = _config_file_override
    if override is not None:
        if not override.path.is_file():
            raise ConfigFileNotFoundError(
                f"Config file '{override.path}' (from {override.source.value}) "
                "does not exist or is not a file."
            )
        return override.path
    for candidate in config_search_paths():
        if candidate.is_file():
            return candidate
    return None


def default_db_file_path() -> Path:
    """Default database file location when not set in config.toml."""
    return Path(user_data_dir(_APP_NAME)) / _DB_FILE_NAME


def default_log_file_path() -> Path:
    """Default log file location when not set in config.toml."""
    return Path(user_log_dir(_APP_NAME)) / _LOG_FILE_NAME
