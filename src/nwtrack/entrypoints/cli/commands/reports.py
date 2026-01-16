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
