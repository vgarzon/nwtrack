"""CLI smoke tests for institution command registration."""

from typer.testing import CliRunner

from nwtrack.entrypoints.cli.app import app

runner = CliRunner()


def test_institutions_command_group_is_registered() -> None:
    """The CLI should expose the institutions command group."""
    result = runner.invoke(app, ["institutions", "--help"])

    assert result.exit_code == 0
    assert "Institution commands" in result.output
    assert "list" in result.output
    assert "create" in result.output
    assert "update" in result.output
    assert "delete" in result.output
