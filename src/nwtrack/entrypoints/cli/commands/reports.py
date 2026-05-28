"""
CLI reporting commands
"""

import sys
from typing import Annotated

import typer

from nwtrack.application.dto import AccountStatusScope, AggregationDimension
from nwtrack.entrypoints.cli.app import reports_app
from nwtrack.entrypoints.cli.ui.console import build_console

console = build_console()


@reports_app.command("balances-category")
def category_summary_report_interactive():
    """
    Generate a networth summary by category interactively.
    """
    import nwtrack.application.use_cases.report_balances_by_category as report_balances

    sys.exit(report_balances.main())


@reports_app.command("networth-history")
def networth_history_report_interactive(
    n_months: int = 12,
    n_years: int | None = None,
    status_scope: Annotated[
        AccountStatusScope,
        typer.Option("--status-scope"),
    ] = AccountStatusScope.HISTORICAL,
):
    """
    Generate a networth history report interactively.

    Args:
        n_months (int): Number of months to include in the report, defaults to 12
        n_years (int | None): Number of years to include in the report,
            overrides n_months if provided
        status_scope: Account status filter, defaults to historical
    """
    import nwtrack.application.use_cases.report_networth_history as report_networth

    if n_years is not None:
        n_months = n_years * 12

    if n_months <= 0:
        console.print(
            "[warning]Number of months must be strictly positive. "
            "Using default of 12 months.[/warning]"
        )
        n_months = 12

    sys.exit(report_networth.main(n_months=n_months, status_scope=status_scope))


@reports_app.command("balances-aggregate")
def balances_aggregate_report(
    month: Annotated[str | None, typer.Option("--month")] = None,
    dimension: Annotated[
        AggregationDimension | None,
        typer.Option("--dimension"),
    ] = None,
    currency: Annotated[str | None, typer.Option("--currency")] = None,
    status_scope: Annotated[
        AccountStatusScope,
        typer.Option("--status-scope"),
    ] = AccountStatusScope.HISTORICAL,
):
    """Generate a grouped single-month balance report."""
    import nwtrack.application.use_cases.report_balances_aggregate as report_balances

    sys.exit(
        report_balances.main(
            month=month,
            dimension=dimension,
            currency_code=currency,
            status_scope=status_scope,
        )
    )


@reports_app.command("balances-aggregate-history")
def balances_aggregate_history_report(
    start_month: Annotated[str | None, typer.Option("--start-month")] = None,
    end_month: Annotated[str | None, typer.Option("--end-month")] = None,
    dimension: Annotated[
        AggregationDimension | None,
        typer.Option("--dimension"),
    ] = None,
    currency: Annotated[str | None, typer.Option("--currency")] = None,
    status_scope: Annotated[
        AccountStatusScope,
        typer.Option("--status-scope"),
    ] = AccountStatusScope.HISTORICAL,
):
    """Generate a grouped history balance report."""
    from nwtrack.application.use_cases import (
        report_balances_aggregate_history as report_balances,
    )

    sys.exit(
        report_balances.main(
            start_month=start_month,
            end_month=end_month,
            dimension=dimension,
            currency_code=currency,
            status_scope=status_scope,
        )
    )
