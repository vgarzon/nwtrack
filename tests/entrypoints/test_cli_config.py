"""CLI smoke tests for config command registration."""

from typer.testing import CliRunner

from nwtrack.entrypoints.cli.app import app

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
