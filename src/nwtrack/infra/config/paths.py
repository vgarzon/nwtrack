"""
Resolve standard per-OS locations for nwtrack's config, data, and log files.
"""

from pathlib import Path

from platformdirs import user_config_dir, user_data_dir, user_log_dir

_APP_NAME = "nwtrack"
_CONFIG_FILE_NAME = "config.toml"
_DB_FILE_NAME = "nwtrack.db"
_LOG_FILE_NAME = "nwtrack.log"


def default_config_dir() -> Path:
    """Highest-priority config directory, used as the write target for `config init`."""
    return Path(user_config_dir(_APP_NAME))


def config_search_paths() -> list[Path]:
    """Candidate `config.toml` locations, in priority order."""
    return [
        default_config_dir() / _CONFIG_FILE_NAME,
        Path.home() / ".config" / _APP_NAME / _CONFIG_FILE_NAME,
        Path("./config") / _APP_NAME / _CONFIG_FILE_NAME,
    ]


def resolve_config_file() -> Path | None:
    """Return the first existing `config.toml` on the search path, or None."""
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
