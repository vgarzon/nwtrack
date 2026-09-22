"""Tests for infra/config/load.py: config.toml parsing and env var overrides."""

from pathlib import Path

import pytest

from nwtrack.application.dto import ConfigValueSource
from nwtrack.infra.config import load as load_module
from nwtrack.infra.config.load import describe_settings, load_settings
from nwtrack.infra.config.settings import Settings


def _write_config(tmp_path: Path, text: str) -> Path:
    config_dir = tmp_path / "pd"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(text, encoding="utf-8")
    return config_file


@pytest.fixture(autouse=True)
def _clear_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "NWTRACK_DATABASE__DB_FILE_PATH",
        "NWTRACK_LOGGING__LOG_FILE",
        "NWTRACK_LOGGING__LOG_FILE_LEVEL",
        "NWTRACK_LOGGING__LOG_ROTATION_MB",
        "NWTRACK_LOGGING__LOG_BACKUP_COUNT",
    ):
        monkeypatch.delenv(key, raising=False)


def test_loads_values_from_well_formed_config_toml(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_file = _write_config(
        tmp_path,
        """
        [database]
        db_file_path = "mydb.sqlite"

        [logging]
        log_file = "mylog.log"
        log_file_level = "DEBUG"
        log_rotation_mb = 5
        log_backup_count = 3
        """,
    )
    monkeypatch.setattr(load_module, "resolve_config_file", lambda: config_file)
    monkeypatch.chdir(tmp_path)

    settings = load_settings()

    assert settings == Settings(
        db_file_path=str((tmp_path / "mydb.sqlite").resolve()),
        log_file=str((tmp_path / "mylog.log").resolve()),
        log_file_level="DEBUG",
        log_rotation_mb=5,
        log_backup_count=3,
    )


def test_missing_config_falls_back_to_defaults(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(load_module, "resolve_config_file", lambda: None)
    monkeypatch.setattr(
        load_module, "default_db_file_path", lambda: tmp_path / "data" / "nwtrack.db"
    )
    monkeypatch.setattr(
        load_module, "default_log_file_path", lambda: tmp_path / "logs" / "nwtrack.log"
    )

    settings = load_settings()

    assert settings.db_file_path == str(tmp_path / "data" / "nwtrack.db")
    assert settings.log_file == str(tmp_path / "logs" / "nwtrack.log")
    assert settings.log_file_level == "INFO"
    assert settings.log_rotation_mb == 10
    assert settings.log_backup_count == 7


def test_empty_string_path_in_toml_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_file = _write_config(
        tmp_path,
        """
        [database]
        db_file_path = ""

        [logging]
        log_file = ""
        """,
    )
    monkeypatch.setattr(load_module, "resolve_config_file", lambda: config_file)
    monkeypatch.setattr(
        load_module, "default_db_file_path", lambda: tmp_path / "data" / "nwtrack.db"
    )
    monkeypatch.setattr(
        load_module, "default_log_file_path", lambda: tmp_path / "logs" / "nwtrack.log"
    )

    settings = load_settings()

    assert settings.db_file_path == str(tmp_path / "data" / "nwtrack.db")
    assert settings.log_file == str(tmp_path / "logs" / "nwtrack.log")


def test_empty_string_env_override_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_file = _write_config(
        tmp_path,
        """
        [database]
        db_file_path = "from-toml.db"
        """,
    )
    monkeypatch.setattr(load_module, "resolve_config_file", lambda: config_file)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NWTRACK_DATABASE__DB_FILE_PATH", "")

    settings = load_settings()

    assert settings.db_file_path == str((tmp_path / "from-toml.db").resolve())


def test_describe_settings_marks_empty_string_path_as_default_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_file = _write_config(
        tmp_path,
        """
        [database]
        db_file_path = ""
        """,
    )
    monkeypatch.setattr(load_module, "resolve_config_file", lambda: config_file)
    monkeypatch.setattr(load_module, "config_search_paths", lambda: [config_file])

    result = describe_settings()

    sources = {f.name: f.source for f in result.fields}
    assert sources["db_file_path"] == ConfigValueSource.DEFAULT


def test_malformed_toml_raises_clear_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_file = _write_config(tmp_path, "not valid = = toml")
    monkeypatch.setattr(load_module, "resolve_config_file", lambda: config_file)

    with pytest.raises(ValueError, match="invalid TOML syntax"):
        load_settings()


def test_wrong_type_raises_clear_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_file = _write_config(
        tmp_path,
        """
        [logging]
        log_rotation_mb = "ten"
        """,
    )
    monkeypatch.setattr(load_module, "resolve_config_file", lambda: config_file)

    with pytest.raises(ValueError, match="log_rotation_mb"):
        load_settings()


@pytest.mark.parametrize(
    ("env_var", "env_value", "field", "expected"),
    [
        ("NWTRACK_DATABASE__DB_FILE_PATH", ":memory:", "db_file_path", ":memory:"),
        ("NWTRACK_LOGGING__LOG_FILE_LEVEL", "WARNING", "log_file_level", "WARNING"),
        ("NWTRACK_LOGGING__LOG_ROTATION_MB", "42", "log_rotation_mb", 42),
        ("NWTRACK_LOGGING__LOG_BACKUP_COUNT", "2", "log_backup_count", 2),
    ],
)
def test_env_var_overrides_toml_value(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    env_var: str,
    env_value: str,
    field: str,
    expected: object,
) -> None:
    config_file = _write_config(
        tmp_path,
        """
        [database]
        db_file_path = "from-toml.db"

        [logging]
        log_file = "from-toml.log"
        log_file_level = "INFO"
        log_rotation_mb = 10
        log_backup_count = 7
        """,
    )
    monkeypatch.setattr(load_module, "resolve_config_file", lambda: config_file)
    monkeypatch.setenv(env_var, env_value)

    settings = load_settings()

    assert getattr(settings, field) == expected


def test_log_file_env_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_file = _write_config(
        tmp_path,
        """
        [logging]
        log_file = "from-toml.log"
        """,
    )
    monkeypatch.setattr(load_module, "resolve_config_file", lambda: config_file)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NWTRACK_LOGGING__LOG_FILE", "overridden.log")

    settings = load_settings()

    assert settings.log_file == str((tmp_path / "overridden.log").resolve())


def test_describe_settings_marks_file_env_and_default_sources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_file = _write_config(
        tmp_path,
        """
        [database]
        db_file_path = "from-toml.db"

        [logging]
        log_file = "from-toml.log"
        """,
    )
    monkeypatch.setattr(load_module, "resolve_config_file", lambda: config_file)
    monkeypatch.setattr(load_module, "config_search_paths", lambda: [config_file])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NWTRACK_LOGGING__LOG_FILE_LEVEL", "DEBUG")

    result = describe_settings()

    sources = {f.name: f.source for f in result.fields}
    assert sources["db_file_path"] == ConfigValueSource.FILE
    assert sources["log_file"] == ConfigValueSource.FILE
    assert sources["log_file_level"] == ConfigValueSource.ENV
    assert sources["log_rotation_mb"] == ConfigValueSource.DEFAULT
    assert sources["log_backup_count"] == ConfigValueSource.DEFAULT

    values = {f.name: f.value for f in result.fields}
    assert values["log_file_level"] == "DEBUG"

    assert len(result.search_paths) == 1
    assert result.search_paths[0].path == config_file
    assert result.search_paths[0].exists is True
    assert result.search_paths[0].is_active is True


def test_describe_settings_marks_no_path_active_when_none_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    candidate_a = tmp_path / "a" / "config.toml"
    candidate_b = tmp_path / "b" / "config.toml"
    monkeypatch.setattr(load_module, "resolve_config_file", lambda: None)
    monkeypatch.setattr(
        load_module, "config_search_paths", lambda: [candidate_a, candidate_b]
    )

    result = describe_settings()

    assert all(not p.exists for p in result.search_paths)
    assert all(not p.is_active for p in result.search_paths)
    sources = {f.name: f.source for f in result.fields}
    assert all(s == ConfigValueSource.DEFAULT for s in sources.values())
