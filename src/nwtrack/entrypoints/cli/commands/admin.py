"""CLI admin commands for database remediation workflows."""

from pathlib import Path

import typer

from nwtrack.entrypoints.cli.app import admin_app


@admin_app.command("list-unassigned")
def list_unassigned() -> None:
    """List accounts that have no institution assigned."""
    import nwtrack.application.use_cases.admin_list_unassigned as uc

    uc.main()


@admin_app.command("assign-institutions")
def assign_institutions() -> None:
    """Interactively assign institutions to accounts that have none."""
    import nwtrack.application.use_cases.admin_assign_institutions as uc

    uc.main()


@admin_app.command("seed-status-history")
def seed_status_history() -> None:
    """Seed account_status_history from balance history and current account status."""
    import nwtrack.application.use_cases.admin_seed_status_history as uc

    uc.main()


@admin_app.command("create-sample-db")
def create_sample_db(
    path: Path = typer.Argument(
        ...,
        help="New SQLite file to create. Must not already exist.",
        dir_okay=False,
    ),
) -> None:
    """Create a new database filled with minimal sample data (for demos).

    Never overwrites: fails if PATH already exists. Does not change your
    configuration; the command prints how to switch to the new database.
    """
    import nwtrack.application.use_cases.admin_create_sample_db as uc

    raise typer.Exit(code=uc.main(path))
