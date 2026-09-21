"""Tests for the InitConfig use case."""

from pathlib import Path

from nwtrack.application.use_cases.init_config import InitConfig


class MockInitConfigPresenter:
    def __init__(self, confirm_overwrite: bool = True) -> None:
        self._confirm_overwrite = confirm_overwrite
        self.calls: list[str] = []
        self.shown_target: Path | None = None
        self.shown_success: Path | None = None

    def show_target_path(self, path: Path) -> None:
        self.calls.append("show_target_path")
        self.shown_target = path

    def confirm_overwrite(self, path: Path) -> bool:
        self.calls.append("confirm_overwrite")
        return self._confirm_overwrite

    def show_success(self, path: Path) -> None:
        self.calls.append("show_success")
        self.shown_success = path

    def show_cancelled(self) -> None:
        self.calls.append("show_cancelled")


def test_writes_default_config_when_none_exists(
    monkeypatch, tmp_path: Path
) -> None:
    config_dir = tmp_path / "config-dir"
    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.default_config_dir",
        lambda: config_dir,
    )
    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.default_db_file_path",
        lambda: tmp_path / "data" / "nwtrack.db",
    )
    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.default_log_file_path",
        lambda: tmp_path / "logs" / "nwtrack.log",
    )
    presenter = MockInitConfigPresenter()

    result = InitConfig(presenter).run()

    target = config_dir / "config.toml"
    assert result.success
    assert result.data == target
    assert target.is_file()
    content = target.read_text()
    assert "[database]" in content
    assert str(tmp_path / "data" / "nwtrack.db") in content
    assert "[logging]" in content
    assert str(tmp_path / "logs" / "nwtrack.log") in content
    assert "confirm_overwrite" not in presenter.calls


def test_declines_overwrite_leaves_file_untouched(
    monkeypatch, tmp_path: Path
) -> None:
    config_dir = tmp_path / "config-dir"
    config_dir.mkdir(parents=True)
    target = config_dir / "config.toml"
    target.write_text("existing content")

    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.default_config_dir",
        lambda: config_dir,
    )
    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.default_db_file_path",
        lambda: tmp_path / "data" / "nwtrack.db",
    )
    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.default_log_file_path",
        lambda: tmp_path / "logs" / "nwtrack.log",
    )
    presenter = MockInitConfigPresenter(confirm_overwrite=False)

    result = InitConfig(presenter).run()

    assert not result.success
    assert target.read_text() == "existing content"
    assert "confirm_overwrite" in presenter.calls
    assert "show_cancelled" in presenter.calls
    assert "show_success" not in presenter.calls


def test_confirms_overwrite_replaces_file(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / "config-dir"
    config_dir.mkdir(parents=True)
    target = config_dir / "config.toml"
    target.write_text("existing content")

    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.default_config_dir",
        lambda: config_dir,
    )
    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.default_db_file_path",
        lambda: tmp_path / "data" / "nwtrack.db",
    )
    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.default_log_file_path",
        lambda: tmp_path / "logs" / "nwtrack.log",
    )
    presenter = MockInitConfigPresenter(confirm_overwrite=True)

    result = InitConfig(presenter).run()

    assert result.success
    assert target.read_text() != "existing content"
    assert "[database]" in target.read_text()
    assert "show_success" in presenter.calls
