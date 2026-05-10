"""CLI smoke tests for tag command registration."""

from typer.testing import CliRunner

from nwtrack.entrypoints.cli.app import app

runner = CliRunner()


def test_tags_command_group_is_registered() -> None:
    """The CLI should expose the tags command group."""
    result = runner.invoke(app, ["tags", "--help"])

    assert result.exit_code == 0
    assert "Tag commands" in result.output
    assert "list" in result.output
    assert "create" in result.output
    assert "update" in result.output
    assert "delete" in result.output
