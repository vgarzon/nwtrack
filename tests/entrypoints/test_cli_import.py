"""CLI smoke tests for import command registration."""

from typer.testing import CliRunner

from nwtrack.entrypoints.cli.app import app

runner = CliRunner()


def test_import_command_group_is_registered() -> None:
    """The CLI should expose the import command group."""
    result = runner.invoke(app, ["import", "--help"])

    assert result.exit_code == 0
    assert "Import commands" in result.output
    assert "tables-csv" in result.output
