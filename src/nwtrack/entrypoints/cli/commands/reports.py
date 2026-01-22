"""
CLI reporting commands
"""

from nwtrack.entrypoints.cli.app import reports_app


@reports_app.command("networth-category")
def category_summary_report_interactive():
    """
    Generate a networth summary by category interactively.
    """
    import nwtrack.application.use_cases.print_summary as print_summary

    print_summary.main()


@reports_app.command("networth-history")
def networth_history_report_interactive(n_months: int = 12):
    """
    Generate a networth history report interactively.

    Args:
        n_months (int): Number of months to include in the report, defaults to 12
    """
    import nwtrack.application.use_cases.report_networth_history as report_networth_history

    if n_months <= 0:
        n_months = 12

    report_networth_history.main(n_months=n_months)
