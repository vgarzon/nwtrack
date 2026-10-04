"""CLI tests for `nwtrack admin create-sample-db`."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from nwtrack.entrypoints.cli.app import app

runner = CliRunner()


@pytest.fixture
def prod_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the configured database at a path that must stay untouched."""
    path = tmp_path / "prod" / "nwtrack.db"
    monkeypatch.setenv("NWTRACK_DATABASE__DB_FILE_PATH", str(path))
    return path


def test_missing_path_argument_is_a_usage_error(prod_db: Path) -> None:
    result = runner.invoke(app, ["admin", "create-sample-db"])

    assert result.exit_code == 2
    assert not prod_db.exists()


def test_success_creates_database_without_touching_configured_one(
    tmp_path: Path, prod_db: Path
) -> None:
    target = tmp_path / "demo.db"

    result = runner.invoke(app, ["admin", "create-sample-db", str(target)])

    assert result.exit_code == 0, result.output
    assert target.is_file() and target.stat().st_size > 0
    assert not prod_db.exists()
    assert not prod_db.parent.exists()
    assert str(target) in result.output.replace("\n", "")
    assert "db_file_path" in result.output
    assert "NWTRACK_DATABASE__DB_FILE_PATH" in result.output


def test_existing_target_exits_nonzero_and_is_unchanged(
    tmp_path: Path, prod_db: Path
) -> None:
    target = tmp_path / "existing.db"
    target.write_bytes(b"real data")

    result = runner.invoke(app, ["admin", "create-sample-db", str(target)])

    assert result.exit_code == 1
    assert "already exists" in result.output.replace("\n", " ")
    assert target.read_bytes() == b"real data"
    assert not prod_db.exists()


def test_other_admin_commands_still_ensure_runtime_schema(
    prod_db: Path,
) -> None:
    runner.invoke(app, ["admin", "list-unassigned"])

    assert prod_db.exists()
