"""Tests for the create-sample-db Rich presenter."""

from pathlib import Path

from rich.console import Console

from nwtrack.application.dto import SampleDatabaseResult
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.adapters.admin_presenters import (
    RichAdminCreateSampleDbPresenter,
)


def _result(path: Path) -> SampleDatabaseResult:
    return SampleDatabaseResult(
        path=path,
        currencies=2,
        institutions=3,
        tags=2,
        accounts=7,
        balances=76,
        first_month=Month(2025, 11),
        last_month=Month(2026, 10),
    )


def test_success_output_has_path_and_activation_guidance(tmp_path: Path) -> None:
    console = Console(record=True, width=500)
    presenter = RichAdminCreateSampleDbPresenter(console)
    path = tmp_path / "demo.db"

    presenter.show_success(_result(path))

    out = console.export_text()
    assert str(path) in out
    assert f'db_file_path = "{path}"' in out
    assert "[database]" in out
    assert f"NWTRACK_DATABASE__DB_FILE_PATH={path}" in out
    assert "No configuration was changed" in out
    assert "7 accounts" in out


def test_error_output_keeps_brackets_literal() -> None:
    console = Console(record=True, width=200)
    RichAdminCreateSampleDbPresenter(console).show_error("/tmp/[x]/demo.db exists")

    assert "/tmp/[x]/demo.db exists" in console.export_text()
