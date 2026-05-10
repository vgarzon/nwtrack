"""CLI smoke tests for export command registration."""

from typer.testing import CliRunner

from nwtrack.entrypoints.cli.app import app

runner = CliRunner()


def test_export_command_group_is_registered() -> None:
    """The CLI should expose the export command group."""
    result = runner.invoke(app, ["export", "--help"])

    assert result.exit_code == 0
    assert "Export commands" in result.output
    assert "tables-csv" in result.output
