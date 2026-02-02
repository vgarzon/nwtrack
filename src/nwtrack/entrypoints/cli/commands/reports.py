"""
CLI reporting commands
"""

from nwtrack.entrypoints.cli.app import reports_app


@reports_app.command("balances-category")
def category_summary_report_interactive():
    """
    Generate a networth summary by category interactively.
    """
    import sys

    import nwtrack.application.use_cases.report_balances_by_category as report_balances

    sys.exit(report_balances.main())


@reports_app.command("networth-history")
def networth_history_report_interactive(n_months: int = 12):
    """
    Generate a networth history report interactively.

    Args:
        n_months (int): Number of months to include in the report, defaults to 12
    """
    import nwtrack.application.use_cases.report_networth_history as report_networth

    if n_months <= 0:
        n_months = 12

    report_networth.main(n_months=n_months)
