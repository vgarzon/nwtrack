"""
Print summary of balances by category.
"""

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
from nwtrack.application.ports.presentation import BalancesByCategoryPresenter
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.services.report_compatibility import (
    to_monthly_category_balances,
    to_networth,
)

logger = logging.getLogger(__name__)


class _SingleMonthAggregationRunner(Protocol):
    """Shared aggregation dependency for the compatibility category report."""

    def run(
        self,
        request: SingleMonthAggregationRequest,
    ) -> OperationResult[SingleMonthAggregationResult]: ...


class ReportBalancesByCategory:
    """Print summary of balances by category."""

    def __init__(
        self,
        fetcher: FetchService,
        presenter: BalancesByCategoryPresenter,
        aggregation_report: _SingleMonthAggregationRunner,
    ) -> None:
        self._fetcher = fetcher
        self._presenter = presenter
        self._aggregation_report = aggregation_report

    def run(self) -> OperationResult:
        """Run the summary service."""
        logger.info("Starting Print Summary Service")
        self._presenter.show_header()

        active_accounts = self._fetcher.get_accounts(active_only=True)

        self._presenter.show_accounts_table(active_accounts, title_prefix="Active")

        balance_counts = self._fetcher.get_balance_count_per_month()
        balance_counts.sort(key=lambda x: x[0], reverse=True)

        n_months = 3
        month = self._presenter.prompt_for_month_choice(balance_counts[:n_months])

        if month is None:
            logger.warning("No month selected. Exiting.")
            self._presenter.show_no_month_selected_message()
            return OperationResult(success=False, error_message="No month selected.")

        balances = self._fetcher.get_month_balances(month, active_only=True)
        self._presenter.show_balances_table(balances, title_suffix=str(month))

        currencies = self._fetcher.get_month_currencies(
            month,
            AccountStatusScope.ACTIVE,
        )
        if len(currencies) > 1:
            message = (
                "Mixed-currency compatibility reporting is not supported yet. "
                "Conversion-based consolidated reporting is not available yet."
            )
            self._presenter.show_error(message)
            return OperationResult(success=False, error_message=message)

        category_result = self._aggregation_report.run(
            SingleMonthAggregationRequest(
                month=month,
                dimension=AggregationDimension.CATEGORY,
                currency_code=currencies[0] if len(currencies) == 1 else None,
                status_scope=AccountStatusScope.ACTIVE,
            )
        )
        if not category_result.success or category_result.data is None:
            error_message = (
                category_result.error_message
                or "Unable to build category compatibility report."
            )
            self._presenter.show_error(error_message)
            return OperationResult(success=False, error_message=error_message)

        category_sides = {
            category.name: category.side
            for category in self._fetcher.get_all_categories()
        }
        monthly_balances = to_monthly_category_balances(
            category_result.data,
            category_sides,
        )
        self._presenter.show_summary_by_category(monthly_balances, str(month))

        currency_code = "USD"
        networth_result = self._aggregation_report.run(
            SingleMonthAggregationRequest(
                month=month,
                dimension=AggregationDimension.SIDE,
                currency_code=currency_code,
                status_scope=AccountStatusScope.ACTIVE,
            )
        )
        if not networth_result.success or networth_result.data is None:
            error_message = (
                networth_result.error_message
                or "Unable to build net worth compatibility report."
            )
            self._presenter.show_error(error_message)
            return OperationResult(success=False, error_message=error_message)
        nw = to_networth(networth_result.data)

        if not nw:
            logger.warning("No net worth data found for %s in %s", month, currency_code)
            self._presenter.show_no_networth_data_warning(month, currency_code)
            return OperationResult(
                success=False, error_message="No net worth data found."
            )
        title_suffix = f"{month} ({currency_code})"
        self._presenter.show_networth_table(nw, title_suffix, form="wide")

        logger.info("Finished Print Summary Service")
        return OperationResult(success=True)


def main() -> int:
    """Main entry point for the report balances by category CLI command.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    from dotenv import load_dotenv

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.use_cases.report_single_month_aggregation import (
        ReportSingleMonthAggregation,
    )
    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.report_presenters import (
        Console,
        RichBalancesByCategoryPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings
    from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory

    load_dotenv()
    setup_logging()

    console_defaults = ConsoleSettings(record=False)

    container = build_base_container()
    container.register(
        Console,
        lambda _: ConsoleFactory(default_settings=console_defaults)(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ReportSingleMonthAggregation,
        lambda c: ReportSingleMonthAggregation(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        BalancesByCategoryPresenter,
        lambda c: RichBalancesByCategoryPresenter(
            fetcher=c.resolve(FetchService),
            console=c.resolve(Console),
        ),
    ).register(
        ReportBalancesByCategory,
        lambda c: ReportBalancesByCategory(
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(BalancesByCategoryPresenter),
            aggregation_report=c.resolve(ReportSingleMonthAggregation),
        ),
    )
    result: OperationResult = container.resolve(ReportBalancesByCategory).run()

    return 0 if result.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
