"""Report grouped balances across an inclusive month range."""

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
from nwtrack.application.ports.presentation import HistoryAggregationReportPresenter
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.report_history_aggregation import (
    ReportHistoryAggregation,
)
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class _HistoryAggregationReportRunner(Protocol):
    """Shared history aggregation use-case dependency for the CLI workflow."""

    def run(
        self,
        request: HistoryAggregationRequest,
    ) -> OperationResult[HistoryAggregationResult]: ...


class _HistoryAggregationFetchService(Protocol):
    """Read-only data needed by the history aggregation CLI workflow."""

    def get_balance_count_per_month(self) -> list[tuple[Month, int]]: ...

    def get_range_currencies(
        self,
        start_month: Month,
        end_month: Month,
        status_scope: AccountStatusScope = AccountStatusScope.HISTORICAL,
    ) -> list[str]: ...


class HistoryAggregatedBalanceReport:
    """CLI workflow for the dedicated grouped history balances report."""

    def __init__(
        self,
        fetcher: _HistoryAggregationFetchService,
        aggregation_report: _HistoryAggregationReportRunner,
        presenter: HistoryAggregationReportPresenter,
    ) -> None:
        self._fetcher = fetcher
        self._aggregation_report = aggregation_report
        self._presenter = presenter

    def run(
        self,
        start_month: Month | None = None,
        end_month: Month | None = None,
        dimension: AggregationDimension | None = None,
        currency_code: str | None = None,
        status_scope: AccountStatusScope = AccountStatusScope.HISTORICAL,
        allow_interactive: bool = True,
    ) -> OperationResult[HistoryAggregationResult]:
        """Run the grouped history report."""
        logger.info("Starting history aggregated balance report")
        self._presenter.show_header()

        resolved_start_month = self._resolve_start_month(start_month, allow_interactive)
        if resolved_start_month is None:
            return OperationResult(
                success=False,
                error_message="No start month selected.",
            )

        resolved_end_month = self._resolve_end_month(end_month, allow_interactive)
        if resolved_end_month is None:
            return OperationResult(
                success=False,
                error_message="No end month selected.",
            )

        resolved_dimension = self._resolve_dimension(dimension, allow_interactive)
        if resolved_dimension is None:
            return OperationResult(
                success=False,
                error_message="No dimension selected.",
            )

        resolved_currency = self._resolve_currency(
            start_month=resolved_start_month,
            end_month=resolved_end_month,
            dimension=resolved_dimension,
            currency_code=currency_code,
            status_scope=status_scope,
            allow_interactive=allow_interactive,
        )
        if not resolved_currency.success:
            return OperationResult(
                success=False,
                error_message=resolved_currency.error_message,
            )

        request = HistoryAggregationRequest(
            start_month=resolved_start_month,
            end_month=resolved_end_month,
            dimension=resolved_dimension,
            currency_code=resolved_currency.data,
            status_scope=status_scope,
        )
        result = self._aggregation_report.run(request)
        if not result.success or result.data is None:
            error_message = (
                result.error_message or "Unable to build aggregated history report."
            )
            error_message = error_message.replace(
                "Provide currency_code",
                "Provide --currency",
            )
            self._presenter.show_error(error_message)
            return OperationResult(success=False, error_message=error_message)

        if not result.data.rows:
            self._presenter.show_no_data_message(
                start_month=resolved_start_month,
                end_month=resolved_end_month,
                dimension=resolved_dimension,
                status_scope=status_scope,
                currency_code=result.data.currency_code,
            )
            return result

        self._presenter.display_history_aggregation_report(result.data)
        logger.info("Finished history aggregated balance report")
        return result

    def _resolve_start_month(
        self,
        start_month: Month | None,
        allow_interactive: bool,
    ) -> Month | None:
        if start_month is not None:
            return start_month
        if not allow_interactive:
            self._presenter.show_error(
                "Start month is required. Provide --start-month."
            )
            return None

        balance_counts = self._fetcher.get_balance_count_per_month()
        balance_counts.sort(key=lambda item: item[0], reverse=True)
        selected_month = self._presenter.prompt_for_start_month_choice(
            balance_counts[:3]
        )
        if selected_month is None:
            self._presenter.show_no_start_month_selected_message()
            return None
        return selected_month

    def _resolve_end_month(
        self,
        end_month: Month | None,
        allow_interactive: bool,
    ) -> Month | None:
        if end_month is not None:
            return end_month
        if not allow_interactive:
            self._presenter.show_error("End month is required. Provide --end-month.")
            return None

        balance_counts = self._fetcher.get_balance_count_per_month()
        balance_counts.sort(key=lambda item: item[0], reverse=True)
        selected_month = self._presenter.prompt_for_end_month_choice(
            balance_counts[:3]
        )
        if selected_month is None:
            self._presenter.show_no_end_month_selected_message()
            return None
        return selected_month

    def _resolve_dimension(
        self,
        dimension: AggregationDimension | None,
        allow_interactive: bool,
    ) -> AggregationDimension | None:
        if dimension is not None:
            return dimension
        if not allow_interactive:
            self._presenter.show_error("Dimension is required. Provide --dimension.")
            return None

        selected_dimension = self._presenter.prompt_for_dimension_choice()
        if selected_dimension is None:
            self._presenter.show_no_dimension_selected_message()
            return None
        return selected_dimension

    def _resolve_currency(
        self,
        start_month: Month,
        end_month: Month,
        dimension: AggregationDimension,
        currency_code: str | None,
        status_scope: AccountStatusScope,
        allow_interactive: bool,
    ) -> OperationResult[str | None]:
        if currency_code is not None or dimension == AggregationDimension.CURRENCY:
            return OperationResult(success=True, data=currency_code)

        currencies = self._fetcher.get_range_currencies(
            start_month,
            end_month,
            status_scope,
        )
        if len(currencies) <= 1:
            return OperationResult(success=True, data=currency_code)
        if not allow_interactive:
            message = (
                "Aggregation requires one currency. "
                "Provide --currency for mixed-currency ranges."
            )
            self._presenter.show_error(message)
            return OperationResult(success=False, error_message=message)

        selected_currency = self._presenter.prompt_for_currency_choice(currencies)
        if selected_currency is None:
            self._presenter.show_no_currency_selected_message()
            return OperationResult(
                success=False,
                error_message="No currency selected.",
            )
        return OperationResult(success=True, data=selected_currency)


def _parse_month(month: str | None) -> Month | None:
    if month is None:
        return None
    return Month.parse(month)


def main(
    start_month: str | None = None,
    end_month: str | None = None,
    dimension: AggregationDimension | None = None,
    currency_code: str | None = None,
    status_scope: AccountStatusScope = AccountStatusScope.HISTORICAL,
) -> int:
    """Main entry point for the grouped history balances report."""
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.report_presenters import (
        RichHistoryAggregationReportPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    load_dotenv()
    setup_logging()

    try:
        parsed_start_month = _parse_month(start_month)
        parsed_end_month = _parse_month(end_month)
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
        ReportHistoryAggregation,
        lambda c: ReportHistoryAggregation(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichHistoryAggregationReportPresenter,
        lambda c: RichHistoryAggregationReportPresenter(
            fetcher=c.resolve(FetchService),
            console=c.resolve(Console),
        ),
    ).register(
        HistoryAggregatedBalanceReport,
        lambda c: HistoryAggregatedBalanceReport(
            fetcher=c.resolve(FetchService),
            aggregation_report=c.resolve(ReportHistoryAggregation),
            presenter=c.resolve(RichHistoryAggregationReportPresenter),
        ),
    )

    result: OperationResult[HistoryAggregationResult] = container.resolve(
        HistoryAggregatedBalanceReport
    ).run(
        start_month=parsed_start_month,
        end_month=parsed_end_month,
        dimension=dimension,
        currency_code=currency_code,
        status_scope=status_scope,
        allow_interactive=True,
    )
    return 0 if result.success else 1
