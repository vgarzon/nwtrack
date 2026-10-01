"""Tests for infra/config/paths.py search-path resolution."""

from pathlib import Path

import pytest

from nwtrack.infra.config import paths


def test_config_search_paths_order(monkeypatch, tmp_path: Path) -> None:
    """Search order is: ./config/nwtrack, ~/.config, platformdirs config dir."""
    monkeypatch.setattr(paths, "user_config_dir", lambda _name: str(tmp_path / "pd"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")

    result = paths.config_search_paths()

    assert result == [
        Path("./config") / "nwtrack" / "config.toml",
        tmp_path / "home" / ".config" / "nwtrack" / "config.toml",
        tmp_path / "pd" / "config.toml",
    ]


def test_resolve_config_file_returns_none_when_missing(
    monkeypatch, tmp_path: Path
) -> None:
    """No config.toml found anywhere on the search path returns None."""
    monkeypatch.setattr(paths, "user_config_dir", lambda _name: str(tmp_path / "pd"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    monkeypatch.chdir(tmp_path)

    assert paths.resolve_config_file() is None


def _search_layout(monkeypatch, tmp_path: Path) -> tuple[Path, Path, Path]:
    """Point all three search locations into tmp_path; return their directories."""
    pd_dir = tmp_path / "pd"
    home_config = tmp_path / "home" / ".config" / "nwtrack"
    project_config = tmp_path / "config" / "nwtrack"
    monkeypatch.setattr(paths, "user_config_dir", lambda _name: str(pd_dir))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    monkeypatch.chdir(tmp_path)
    return pd_dir, home_config, project_config


def _touch_config(directory: Path) -> Path:
    directory.mkdir(parents=True)
    file = directory / "config.toml"
    file.write_text("")
    return file


def test_resolve_config_file_prefers_project_relative(
    monkeypatch, tmp_path: Path
) -> None:
    """./config/nwtrack wins over every other location."""
    pd_dir, home_config, project_config = _search_layout(monkeypatch, tmp_path)
    _touch_config(pd_dir)
    _touch_config(home_config)
    _touch_config(project_config)

    assert paths.resolve_config_file() == Path("./config") / "nwtrack" / "config.toml"


def test_resolve_config_file_prefers_home_config_over_platformdirs(
    monkeypatch, tmp_path: Path
) -> None:
    """~/.config/nwtrack wins over the standard platformdirs location."""
    pd_dir, home_config, _project = _search_layout(monkeypatch, tmp_path)
    _touch_config(pd_dir)
    home_file = _touch_config(home_config)

    assert paths.resolve_config_file() == home_file


def test_resolve_config_file_falls_back_to_platformdirs(
    monkeypatch, tmp_path: Path
) -> None:
    """The standard platformdirs location is the last resort."""
    pd_dir, _home, _project = _search_layout(monkeypatch, tmp_path)
    pd_file = _touch_config(pd_dir)

    assert paths.resolve_config_file() == pd_file


def test_override_bypasses_search_path(monkeypatch, tmp_path: Path) -> None:
    """An existing override is returned even when search-path files exist."""
    pd_dir, _home, project_config = _search_layout(monkeypatch, tmp_path)
    _touch_config(pd_dir)
    _touch_config(project_config)
    explicit = tmp_path / "explicit.toml"
    explicit.write_text("")
    paths.set_config_file_override(
        paths.ConfigFileOverride(explicit, paths.ConfigFileOverrideSource.FLAG)
    )

    assert paths.resolve_config_file() == explicit


@pytest.mark.parametrize(
    "source", [paths.ConfigFileOverrideSource.FLAG, paths.ConfigFileOverrideSource.ENV]
)
def test_missing_override_raises_naming_path_and_source(
    monkeypatch, tmp_path: Path, source: paths.ConfigFileOverrideSource
) -> None:
    """A missing override is a hard error, with no fallback to the search path."""
    pd_dir, _home, _project = _search_layout(monkeypatch, tmp_path)
    _touch_config(pd_dir)
    missing = tmp_path / "missing.toml"
    paths.set_config_file_override(paths.ConfigFileOverride(missing, source))

    with pytest.raises(paths.ConfigFileNotFoundError) as exc_info:
        paths.resolve_config_file()

    assert str(missing) in str(exc_info.value)
    assert source.value in str(exc_info.value)


def test_directory_override_is_an_error(monkeypatch, tmp_path: Path) -> None:
    """An override naming a directory is not a file, so it errors."""
    _search_layout(monkeypatch, tmp_path)
    paths.set_config_file_override(
        paths.ConfigFileOverride(tmp_path, paths.ConfigFileOverrideSource.FLAG)
    )

    with pytest.raises(paths.ConfigFileNotFoundError):
        paths.resolve_config_file()


def test_default_db_and_log_file_paths(monkeypatch, tmp_path: Path) -> None:
    """Default db/log file paths are derived from platformdirs data/log dirs."""
    monkeypatch.setattr(paths, "user_data_dir", lambda _name: str(tmp_path / "data"))
    monkeypatch.setattr(paths, "user_log_dir", lambda _name: str(tmp_path / "logs"))

    assert paths.default_db_file_path() == tmp_path / "data" / "nwtrack.db"
    assert paths.default_log_file_path() == tmp_path / "logs" / "nwtrack.log"
