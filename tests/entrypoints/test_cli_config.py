"""CLI smoke tests for config command registration."""

from pathlib import Path

from typer.testing import CliRunner

from nwtrack.entrypoints.cli.app import app
from nwtrack.infra.config.paths import (
    ConfigFileOverrideSource,
    get_config_file_override,
)

runner = CliRunner()


def test_config_command_group_is_registered() -> None:
    """The CLI should expose the config command group."""
    result = runner.invoke(app, ["config", "--help"])

    assert result.exit_code == 0
    assert "Config commands" in result.output
    assert "init" in result.output
    assert "show" in result.output


def test_config_init_invokes_use_case(monkeypatch) -> None:
    """`nwtrack config init` should invoke the InitConfig use case's main()."""
    calls: list[bool] = []

    def fake_main() -> int:
        calls.append(True)
        return 0

    monkeypatch.setattr(
        "nwtrack.application.use_cases.init_config.main", fake_main
    )

    result = runner.invoke(app, ["config", "init"])

    assert result.exit_code == 0
    assert calls == [True]


def test_config_show_invokes_use_case(monkeypatch) -> None:
    """`nwtrack config show` should invoke the ShowConfig use case's main()."""
    calls: list[bool] = []

    def fake_main() -> int:
        calls.append(True)
        return 0

    monkeypatch.setattr(
        "nwtrack.application.use_cases.show_config.main", fake_main
    )

    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert calls == [True]


def _capture_override(monkeypatch) -> list:
    """Replace `config show`'s use case with one that records the active override."""
    seen: list = []

    def fake_main() -> int:
        seen.append(get_config_file_override())
        return 0

    monkeypatch.setattr("nwtrack.application.use_cases.show_config.main", fake_main)
    return seen


def test_config_file_flag_sets_override(monkeypatch, tmp_path: Path) -> None:
    seen = _capture_override(monkeypatch)
    target = tmp_path / "a.toml"

    result = runner.invoke(app, ["--config-file", str(target), "config", "show"])

    assert result.exit_code == 0
    assert seen[0] is not None
    assert seen[0].path == target.resolve()
    assert seen[0].source == ConfigFileOverrideSource.FLAG


def test_config_file_env_sets_override(monkeypatch, tmp_path: Path) -> None:
    seen = _capture_override(monkeypatch)
    target = tmp_path / "b.toml"
    monkeypatch.setenv("NWTRACK_CONFIG_FILE", str(target))

    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    assert seen[0].path == target.resolve()
    assert seen[0].source == ConfigFileOverrideSource.ENV


def test_config_file_flag_beats_env(monkeypatch, tmp_path: Path) -> None:
    seen = _capture_override(monkeypatch)
    monkeypatch.setenv("NWTRACK_CONFIG_FILE", str(tmp_path / "env.toml"))
    flag = tmp_path / "flag.toml"

    result = runner.invoke(app, ["--config-file", str(flag), "config", "show"])

    assert result.exit_code == 0
    assert seen[0].path == flag.resolve()
    assert seen[0].source == ConfigFileOverrideSource.FLAG


def test_empty_env_is_ignored(monkeypatch) -> None:
    seen = _capture_override(monkeypatch)
    monkeypatch.setenv("NWTRACK_CONFIG_FILE", "")

    runner.invoke(app, ["config", "show"])

    assert seen == [None]


def test_override_does_not_leak_into_next_invocation(
    monkeypatch, tmp_path: Path
) -> None:
    seen = _capture_override(monkeypatch)

    runner.invoke(app, ["--config-file", str(tmp_path / "a.toml"), "config", "show"])
    runner.invoke(app, ["config", "show"])

    assert seen[0] is not None
    assert seen[1] is None


def test_missing_override_file_blocks_non_config_commands(
    monkeypatch, tmp_path: Path
) -> None:
    """A missing explicit file is a hard error when a command needs settings."""
    from nwtrack.infra.config.paths import ConfigFileNotFoundError

    missing = tmp_path / "missing.toml"

    result = runner.invoke(app, ["--config-file", str(missing), "accounts", "list"])

    assert result.exit_code != 0
    assert isinstance(result.exception, ConfigFileNotFoundError)
    assert str(missing) in str(result.exception)
    assert "--config-file" in str(result.exception)


def test_config_init_runs_with_missing_override_file(
    monkeypatch, tmp_path: Path
) -> None:
    """`config init` must not be blocked by the file it is about to create."""
    target = tmp_path / "new" / "config.toml"

    result = runner.invoke(app, ["--config-file", str(target), "config", "init"])

    assert result.exit_code == 0
    assert target.is_file()


def test_cli_app_does_not_import_click_directly() -> None:
    """click is only a transitive dependency of Typer and is absent from newer
    Typer installs; importing it directly breaks `uv tool install`."""
    import nwtrack.entrypoints.cli.app as app_module

    assert app_module.__file__ is not None
    assert "click" not in Path(app_module.__file__).read_text()
