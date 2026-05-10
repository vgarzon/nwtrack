"""Report grouped balances for one month and one aggregation dimension."""

from __future__ import annotations

import logging

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    OperationResult,
    SingleMonthAggregationRequest,
    SingleMonthAggregationResult,
)
from nwtrack.application.ports.presentation import SingleMonthAggregationReportPresenter
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.report_single_month_aggregation import (
    ReportSingleMonthAggregation,
)
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class SingleMonthAggregatedBalanceReport:
    """CLI workflow for the dedicated single-month grouped balances report."""

    def __init__(
        self,
        fetcher: FetchService,
        aggregation_report: ReportSingleMonthAggregation,
        presenter: SingleMonthAggregationReportPresenter,
    ) -> None:
        self._fetcher = fetcher
        self._aggregation_report = aggregation_report
        self._presenter = presenter

    def run(
        self,
        month: Month | None = None,
        dimension: AggregationDimension | None = None,
        currency_code: str | None = None,
        status_scope: AccountStatusScope = AccountStatusScope.ACTIVE,
        allow_interactive: bool = True,
    ) -> OperationResult[SingleMonthAggregationResult]:
        """Run the grouped single-month report."""
        logger.info("Starting single-month aggregated balance report")
        self._presenter.show_header()

        if month is None:
            message = "Month is required. Provide --month."
            self._presenter.show_error(message)
            return OperationResult(success=False, error_message=message)

        if dimension is None:
            message = "Dimension is required. Provide --dimension."
            self._presenter.show_error(message)
            return OperationResult(success=False, error_message=message)

        request = SingleMonthAggregationRequest(
            month=month,
            dimension=dimension,
            currency_code=currency_code,
            status_scope=status_scope,
        )
        result = self._aggregation_report.run(request)
        if not result.success or result.data is None:
            error_message = result.error_message or "Unable to build aggregated report."
            self._presenter.show_error(error_message)
            return OperationResult(success=False, error_message=error_message)

        if not result.data.groups:
            self._presenter.show_no_data_message(
                month=month,
                dimension=dimension,
                status_scope=status_scope,
                currency_code=result.data.currency_code,
            )
            return result

        self._presenter.display_aggregation_report(result.data)
        logger.info("Finished single-month aggregated balance report")
        return result


def _parse_month(month: str | None) -> Month | None:
    if month is None:
        return None
    return Month.parse(month)


def main(
    month: str | None = None,
    dimension: AggregationDimension | None = None,
    currency_code: str | None = None,
    status_scope: AccountStatusScope = AccountStatusScope.ACTIVE,
) -> int:
    """Main entry point for the grouped single-month balances report."""
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.report_presenters import (
        RichSingleMonthAggregationReportPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    load_dotenv()
    setup_logging()

    try:
        parsed_month = _parse_month(month)
    except ValueError:
        console = build_console()
        console.print("[error]Invalid month format. Please use YYYY-MM.[/error]")
        return 1

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ReportSingleMonthAggregation,
        lambda c: ReportSingleMonthAggregation(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichSingleMonthAggregationReportPresenter,
        lambda c: RichSingleMonthAggregationReportPresenter(
            fetcher=c.resolve(FetchService),
            console=c.resolve(Console),
        ),
    ).register(
        SingleMonthAggregatedBalanceReport,
        lambda c: SingleMonthAggregatedBalanceReport(
            fetcher=c.resolve(FetchService),
            aggregation_report=c.resolve(ReportSingleMonthAggregation),
            presenter=c.resolve(RichSingleMonthAggregationReportPresenter),
        ),
    )

    result: OperationResult[SingleMonthAggregationResult] = container.resolve(
        SingleMonthAggregatedBalanceReport
    ).run(
        month=parsed_month,
        dimension=dimension,
        currency_code=currency_code,
        status_scope=status_scope,
        allow_interactive=True,
    )
    return 0 if result.success else 1
