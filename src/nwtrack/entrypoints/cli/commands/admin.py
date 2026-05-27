"""CLI admin commands for database remediation workflows."""

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
