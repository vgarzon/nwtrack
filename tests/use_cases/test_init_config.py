"""Tests for the InitConfig use case."""

from pathlib import Path

from nwtrack.application.use_cases.init_config import InitConfig


class MockInitConfigPresenter:
    def __init__(
        self, confirm_overwrite: bool = True, confirm_shadow: bool = True
    ) -> None:
        self._confirm_overwrite = confirm_overwrite
        self._confirm_shadow = confirm_shadow
        self.calls: list[str] = []
        self.shown_target: Path | None = None
        self.shown_success: Path | None = None
        self.shadow_args: tuple[Path, Path] | None = None

    def show_target_path(self, path: Path) -> None:
        self.calls.append("show_target_path")
        self.shown_target = path

    def confirm_overwrite(self, path: Path) -> bool:
        self.calls.append("confirm_overwrite")
        return self._confirm_overwrite

    def confirm_shadow(self, target_path: Path, shadowed_path: Path) -> bool:
        self.calls.append("confirm_shadow")
        self.shadow_args = (target_path, shadowed_path)
        return self._confirm_shadow

    def show_success(self, path: Path) -> None:
        self.calls.append("show_success")
        self.shown_success = path

    def show_cancelled(self) -> None:
        self.calls.append("show_cancelled")


def _patch_defaults(monkeypatch, tmp_path: Path, config_dir: Path) -> None:
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


def _no_shadow(monkeypatch) -> None:
    """No existing config.toml anywhere on the search path."""
    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.resolve_config_file",
        lambda: None,
    )


def test_writes_default_config_when_none_exists(
    monkeypatch, tmp_path: Path
) -> None:
    config_dir = tmp_path / "config-dir"
    _patch_defaults(monkeypatch, tmp_path, config_dir)
    _no_shadow(monkeypatch)
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
    assert "confirm_shadow" not in presenter.calls


def test_declines_overwrite_leaves_file_untouched(
    monkeypatch, tmp_path: Path
) -> None:
    config_dir = tmp_path / "config-dir"
    config_dir.mkdir(parents=True)
    target = config_dir / "config.toml"
    target.write_text("existing content")

    _patch_defaults(monkeypatch, tmp_path, config_dir)
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

    _patch_defaults(monkeypatch, tmp_path, config_dir)
    presenter = MockInitConfigPresenter(confirm_overwrite=True)

    result = InitConfig(presenter).run()

    assert result.success
    assert target.read_text() != "existing content"
    assert "[database]" in target.read_text()
    assert "show_success" in presenter.calls


def test_declines_shadow_leaves_no_file_written(
    monkeypatch, tmp_path: Path
) -> None:
    """No file at the target location, but a lower-priority config.toml is
    active — declining the shadow warning must not write anything."""
    config_dir = tmp_path / "config-dir"
    shadowed = tmp_path / "lower-priority" / "config.toml"
    shadowed.parent.mkdir(parents=True)
    shadowed.write_text("lower priority content")

    _patch_defaults(monkeypatch, tmp_path, config_dir)
    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.resolve_config_file",
        lambda: shadowed,
    )
    presenter = MockInitConfigPresenter(confirm_shadow=False)

    result = InitConfig(presenter).run()

    assert not result.success
    assert not (config_dir / "config.toml").exists()
    assert "confirm_shadow" in presenter.calls
    assert presenter.shadow_args == (config_dir / "config.toml", shadowed)
    assert "show_cancelled" in presenter.calls
    assert "show_success" not in presenter.calls


def test_confirms_shadow_writes_target_file(monkeypatch, tmp_path: Path) -> None:
    """Confirming the shadow warning writes the new file at the target
    (higher-priority) location; the shadowed file is left untouched."""
    config_dir = tmp_path / "config-dir"
    shadowed = tmp_path / "lower-priority" / "config.toml"
    shadowed.parent.mkdir(parents=True)
    shadowed.write_text("lower priority content")

    _patch_defaults(monkeypatch, tmp_path, config_dir)
    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.resolve_config_file",
        lambda: shadowed,
    )
    presenter = MockInitConfigPresenter(confirm_shadow=True)

    result = InitConfig(presenter).run()

    target = config_dir / "config.toml"
    assert result.success
    assert result.data == target
    assert target.is_file()
    assert "[database]" in target.read_text()
    assert shadowed.read_text() == "lower priority content"
    assert "show_success" in presenter.calls
