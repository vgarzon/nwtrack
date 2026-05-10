"""CLI smoke tests for report command registration."""

from typer.testing import CliRunner

from nwtrack.entrypoints.cli.app import app

runner = CliRunner()


def test_reports_command_group_includes_balances_aggregate() -> None:
    """The CLI should expose the new balances aggregate command."""
    result = runner.invoke(app, ["reports", "--help"])

    assert result.exit_code == 0
    assert "Report commands" in result.output
    assert "balances-aggregate" in result.output
    assert "balances-category" in result.output
    assert "networth-history" in result.output
