"""CLI smoke tests for balance command registration."""

from typer.testing import CliRunner

from nwtrack.entrypoints.cli.app import app

runner = CliRunner()


def test_balances_command_group_includes_create() -> None:
    """The CLI should expose the new balances create command."""
    result = runner.invoke(app, ["balances", "--help"])

    assert result.exit_code == 0
    assert "Balance commands" in result.output
    assert "create" in result.output
    assert "update" in result.output
    assert "delete" in result.output
    assert "roll" in result.output
    assert "transfer" in result.output
