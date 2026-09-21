"""Tests for the CLI entry point's config-error handling."""

import pytest

from nwtrack.entrypoints.cli import main as main_module


def test_main_reports_config_errors_cleanly(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A ValueError from config loading should exit(1) with a clean message,
    not an unhandled traceback."""

    def raise_value_error() -> None:
        raise ValueError("Config value '[logging].log_rotation_mb' must be an integer.")

    monkeypatch.setattr(main_module, "app", raise_value_error)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Configuration error" in captured.err
    assert "log_rotation_mb" in captured.err
