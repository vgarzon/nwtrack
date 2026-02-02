"""
CLI reporting commands
"""

import sys

from rich.console import Console

from nwtrack.entrypoints.cli.app import reports_app

console = Console()


@reports_app.command("balances-category")
def category_summary_report_interactive():
    """
    Generate a networth summary by category interactively.
    """
    import nwtrack.application.use_cases.report_balances_by_category as report_balances

    sys.exit(report_balances.main())


@reports_app.command("networth-history")
def networth_history_report_interactive(n_months: int = 12, n_years: int | None = None):
    """
    Generate a networth history report interactively.

    Args:
        n_months (int): Number of months to include in the report, defaults to 12
        n_years (int | None): Number of years to include in the report,
            overrides n_months if provided
    """
    import nwtrack.application.use_cases.report_networth_history as report_networth

    if n_years is not None:
        n_months = n_years * 12

    if n_months <= 0:
        console.print(
            "[orange3]Number of months must be strictly positive. "
            "Using default of 12 months.[/orange3]"
        )
        n_months = 12

    sys.exit(report_networth.main(n_months=n_months))
