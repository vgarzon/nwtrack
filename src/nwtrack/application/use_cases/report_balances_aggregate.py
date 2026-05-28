"""Report grouped balances for one month and one aggregation dimension."""

from __future__ import annotations

import logging
from typing import Protocol

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


class _AggregationReportRunner(Protocol):
    """Shared aggregation use-case dependency for the CLI workflow."""

    def run(
        self,
        request: SingleMonthAggregationRequest,
    ) -> OperationResult[SingleMonthAggregationResult]: ...


class _AggregationReportFetchService(Protocol):
    """Read-only data needed by the CLI workflow."""

    def get_balance_count_per_month(self) -> list[tuple[Month, int]]: ...

    def get_month_currencies(
        self,
        month: Month,
        status_scope: AccountStatusScope = AccountStatusScope.HISTORICAL,
    ) -> list[str]: ...


class SingleMonthAggregatedBalanceReport:
    """CLI workflow for the dedicated single-month grouped balances report."""

    def __init__(
        self,
        fetcher: _AggregationReportFetchService,
        aggregation_report: _AggregationReportRunner,
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
        status_scope: AccountStatusScope = AccountStatusScope.HISTORICAL,
        allow_interactive: bool = True,
    ) -> OperationResult[SingleMonthAggregationResult]:
        """Run the grouped single-month report."""
        logger.info("Starting single-month aggregated balance report")
        self._presenter.show_header()

        resolved_month = self._resolve_month(month, allow_interactive)
        if resolved_month is None:
            return OperationResult(success=False, error_message="No month selected.")

        resolved_dimension = self._resolve_dimension(dimension, allow_interactive)
        if resolved_dimension is None:
            return OperationResult(
                success=False,
                error_message="No dimension selected.",
            )

        resolved_currency = self._resolve_currency(
            month=resolved_month,
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

        request = SingleMonthAggregationRequest(
            month=resolved_month,
            dimension=resolved_dimension,
            currency_code=resolved_currency.data,
            status_scope=status_scope,
        )
        result = self._aggregation_report.run(request)
        if not result.success or result.data is None:
            error_message = result.error_message or "Unable to build aggregated report."
            error_message = error_message.replace(
                "Provide currency_code", "Provide --currency"
            )
            self._presenter.show_error(error_message)
            return OperationResult(success=False, error_message=error_message)

        if not result.data.groups:
            self._presenter.show_no_data_message(
                month=resolved_month,
                dimension=resolved_dimension,
                status_scope=status_scope,
                currency_code=result.data.currency_code,
            )
            return result

        self._presenter.display_aggregation_report(result.data)
        logger.info("Finished single-month aggregated balance report")
        return result

    def _resolve_month(
        self,
        month: Month | None,
        allow_interactive: bool,
    ) -> Month | None:
        if month is not None:
            return month
        if not allow_interactive:
            self._presenter.show_error("Month is required. Provide --month.")
            return None

        balance_counts = self._fetcher.get_balance_count_per_month()
        balance_counts.sort(key=lambda item: item[0], reverse=True)
        selected_month = self._presenter.prompt_for_month_choice(balance_counts[:3])
        if selected_month is None:
            self._presenter.show_no_month_selected_message()
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
        month: Month,
        dimension: AggregationDimension,
        currency_code: str | None,
        status_scope: AccountStatusScope,
        allow_interactive: bool,
    ) -> OperationResult[str | None]:
        if currency_code is not None or dimension == AggregationDimension.CURRENCY:
            return OperationResult(success=True, data=currency_code)

        currencies = self._fetcher.get_month_currencies(month, status_scope)
        if len(currencies) <= 1:
            return OperationResult(success=True, data=currency_code)
        if not allow_interactive:
            message = (
                "Aggregation requires one currency. "
                "Provide --currency for mixed-currency months."
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
    month: str | None = None,
    dimension: AggregationDimension | None = None,
    currency_code: str | None = None,
    status_scope: AccountStatusScope = AccountStatusScope.HISTORICAL,
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
