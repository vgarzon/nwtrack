"""
Print summary of balances by category.
"""

import logging

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import BalancesByCategoryPresenter
from nwtrack.application.services.fetch import FetchService

logger = logging.getLogger(__name__)


class ReportBalancesByCategory:
    """Print summary of balances by category."""

    def __init__(
        self,
        fetcher: FetchService,
        presenter: BalancesByCategoryPresenter,
    ) -> None:
        self._fetcher = fetcher
        self._presenter = presenter

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
        monthly_balances = self._fetcher.get_monthly_balance_total_by_category(month)
        self._presenter.show_summary_by_category(monthly_balances, str(month))

        # TODO: Handle currency selection
        currency_code = "USD"
        nw = self._fetcher.get_networth(month, currency_code=currency_code)

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
        ),
    )
    result: OperationResult = container.resolve(ReportBalancesByCategory).run()

    return 0 if result.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
