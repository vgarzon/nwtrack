"""
Display network history and total change over a specified period.
"""

from __future__ import annotations

import logging
from typing import Protocol

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    HistoryAggregationRequest,
    HistoryAggregationResult,
    OperationResult,
)
from nwtrack.application.ports.presentation import NetworthHistoryPresenter
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.services.report_compatibility import to_networth_history

logger = logging.getLogger(__name__)


class _HistoryAggregationRunner(Protocol):
    """Shared history aggregation dependency for legacy net-worth reporting."""

    def run(
        self,
        request: HistoryAggregationRequest,
    ) -> OperationResult[HistoryAggregationResult]: ...


class NetworthHistoryReport:
    """Print networth history report."""

    def __init__(
        self,
        fetcher: FetchService,
        presenter: NetworthHistoryPresenter,
        aggregation_report: _HistoryAggregationRunner,
    ) -> None:
        self._fetcher = fetcher
        self._presenter = presenter
        self._aggregation_report = aggregation_report

    def run(
        self, n_months: int = 12, currency_code: str = "USD"
    ) -> OperationResult[None]:
        """Run the networth history report.

        Args:
            n_months: Number of months to include in the report, defaults to 12
            currency_code: Currency code for the report, defaults to "USD"

        Returns:
            OperationResult indicating success/failure
        """
        logger.info("Starting Networth History Report Service")
        self._presenter.show_header()

        available_months = self._fetcher.get_available_aggregation_months(
            AggregationDimension.SIDE,
            currency_code=currency_code,
            status_scope=AccountStatusScope.ACTIVE,
        )
        selected_months = available_months[-n_months:]

        if not selected_months:
            logger.warning("No net worth history found in %s", currency_code)
            self._presenter.show_no_data_warning(currency_code)
            return OperationResult(success=False, error_message="No data found")

        if len(selected_months) < n_months:
            logger.warning(
                "Requested %d months of net worth history, but only %d found.",
                n_months,
                len(selected_months),
            )
            self._presenter.show_partial_data_warning(
                n_months,
                len(selected_months),
                currency_code,
            )

        aggregation_result = self._aggregation_report.run(
            HistoryAggregationRequest(
                start_month=selected_months[0],
                end_month=selected_months[-1],
                dimension=AggregationDimension.SIDE,
                currency_code=currency_code,
                status_scope=AccountStatusScope.ACTIVE,
            )
        )
        if not aggregation_result.success or aggregation_result.data is None:
            logger.warning("No net worth history found in %s", currency_code)
            self._presenter.show_no_data_warning(currency_code)
            return OperationResult(success=False, error_message="No data found")

        nws = to_networth_history(aggregation_result.data)
        if not nws:
            logger.warning("No net worth history found in %s", currency_code)
            self._presenter.show_no_data_warning(currency_code)
            return OperationResult(success=False, error_message="No data found")

        # Ensure chronological order
        nws.sort(key=lambda x: x.month)

        # Display results
        self._presenter.display_networth_history(nws, currency_code)
        self._presenter.display_total_change(nws, currency_code)

        logger.info("Finished Networth History Report Service")
        return OperationResult(success=True)


def main(n_months: int = 12, currency_code: str = "USD") -> int:
    """Main entry point for networth history report script.

    Args:
        n_months: Number of months to include in the report, defaults to 12
        currency_code: Currency code for the report, defaults to "USD"

    Returns:
        Exit code: 0 on success, 1 on failure
    """
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.use_cases.report_history_aggregation import (
        ReportHistoryAggregation,
    )
    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.report_presenters import (
        RichNetworthHistoryPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    load_dotenv()
    setup_logging()

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ReportHistoryAggregation,
        lambda c: ReportHistoryAggregation(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichNetworthHistoryPresenter,
        lambda c: RichNetworthHistoryPresenter(console=c.resolve(Console)),
    ).register(
        NetworthHistoryReport,
        lambda c: NetworthHistoryReport(
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(RichNetworthHistoryPresenter),
            aggregation_report=c.resolve(ReportHistoryAggregation),
        ),
    )

    result: OperationResult[None] = container.resolve(NetworthHistoryReport).run(
        n_months, currency_code
    )
    return 0 if result.success else 1


if __name__ == "__main__":
    import sys

    if sys.argv[1:]:
        n_months = int(sys.argv[1])
    else:
        n_months = 12

    sys.exit(main(n_months))
