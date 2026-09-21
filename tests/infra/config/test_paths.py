"""Tests for infra/config/paths.py search-path resolution."""

from pathlib import Path

from nwtrack.infra.config import paths


def test_config_search_paths_order(monkeypatch, tmp_path: Path) -> None:
    """Search order is: platformdirs config dir, ~/.config, ./config/nwtrack."""
    monkeypatch.setattr(paths, "user_config_dir", lambda _name: str(tmp_path / "pd"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")

    result = paths.config_search_paths()

    assert result == [
        tmp_path / "pd" / "config.toml",
        tmp_path / "home" / ".config" / "nwtrack" / "config.toml",
        Path("./config") / "nwtrack" / "config.toml",
    ]


def test_resolve_config_file_returns_none_when_missing(
    monkeypatch, tmp_path: Path
) -> None:
    """No config.toml found anywhere on the search path returns None."""
    monkeypatch.setattr(paths, "user_config_dir", lambda _name: str(tmp_path / "pd"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    monkeypatch.chdir(tmp_path)

    assert paths.resolve_config_file() is None


def test_resolve_config_file_prefers_platformdirs_location(
    monkeypatch, tmp_path: Path
) -> None:
    """The platformdirs default location wins when a file exists there."""
    pd_dir = tmp_path / "pd"
    pd_dir.mkdir()
    (pd_dir / "config.toml").write_text("")
    home_config = tmp_path / "home" / ".config" / "nwtrack"
    home_config.mkdir(parents=True)
    (home_config / "config.toml").write_text("")

    monkeypatch.setattr(paths, "user_config_dir", lambda _name: str(pd_dir))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")

    assert paths.resolve_config_file() == pd_dir / "config.toml"


def test_resolve_config_file_falls_back_to_home_config(
    monkeypatch, tmp_path: Path
) -> None:
    """The ~/.config fallback is used when the platformdirs location has no file."""
    home_config = tmp_path / "home" / ".config" / "nwtrack"
    home_config.mkdir(parents=True)
    (home_config / "config.toml").write_text("")

    monkeypatch.setattr(paths, "user_config_dir", lambda _name: str(tmp_path / "pd"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")

    assert paths.resolve_config_file() == home_config / "config.toml"


def test_resolve_config_file_falls_back_to_project_relative(
    monkeypatch, tmp_path: Path
) -> None:
    """The ./config/nwtrack fallback is used as the last resort."""
    monkeypatch.setattr(paths, "user_config_dir", lambda _name: str(tmp_path / "pd"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    monkeypatch.chdir(tmp_path)
    project_config = tmp_path / "config" / "nwtrack"
    project_config.mkdir(parents=True)
    (project_config / "config.toml").write_text("")

    assert paths.resolve_config_file() == Path("./config") / "nwtrack" / "config.toml"


def test_default_db_and_log_file_paths(monkeypatch, tmp_path: Path) -> None:
    """Default db/log file paths are derived from platformdirs data/log dirs."""
    monkeypatch.setattr(paths, "user_data_dir", lambda _name: str(tmp_path / "data"))
    monkeypatch.setattr(paths, "user_log_dir", lambda _name: str(tmp_path / "logs"))

    assert paths.default_db_file_path() == tmp_path / "data" / "nwtrack.db"
    assert paths.default_log_file_path() == tmp_path / "logs" / "nwtrack.log"
