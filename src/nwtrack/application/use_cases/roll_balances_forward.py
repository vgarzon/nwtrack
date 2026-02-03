"""
Roll balances forward to next available month.
"""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import BalancesRollForwardPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class RollBalancesUpdater:
    """Update account balances interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        presenter: BalancesRollForwardPresenter,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        logger.info("Starting Roll Balances Forward Updater")
        self._presenter.show_header()
        target_month = self.get_next_free_month()

        proceed = self._presenter.confirm_target_month(target_month)
        if not proceed:
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="User cancelled.")

        source_month = self._select_month()
        if source_month is None:
            logger.info("User cancelled month selection.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="User cancelled.")

        if not self._fetcher.check_month_in_balances(source_month):
            _msg = f"No balances found for month {source_month}"
            logger.error(_msg)
            return OperationResult(success=False, error_message=_msg)

        proceed = self._presenter.prompt_to_confirm_months(source_month, target_month)
        if not proceed:
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="User cancelled.")

        success = self._copy_monthly_balances(source_month, target_month)
        if not success:
            _msg = f"Failed to copy balances from {source_month} to {target_month}."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        balance_count = self._fetcher.get_balance_count_for_month(target_month)
        self._presenter.show_success(f"Copied {balance_count} balance entries.")

        # TODO: Handle currency selection
        currency_code = "USD"
        nw = self._fetcher.get_networth(target_month, currency_code=currency_code)
        if nw:
            self._presenter.display_networth(
                nw, title_suffix=f"{target_month} ({currency_code})"
            )
        else:
            logger.warning(
                "No net worth data found for %s in %s", target_month, currency_code
            )
        logger.info("Finished Roll Balances Forward Updater")
        return OperationResult(success=True)

    def get_next_free_month(self) -> Month:
        """Get the next month that does not have balances yet.

        Returns:
            Month: Next month without balances.
        """
        recent_months = self._fetcher.get_recent_months()
        latest_month = recent_months[0]
        next_month = latest_month.increment()
        return next_month

    def _copy_monthly_balances(self, source_month: Month, target_month: Month) -> bool:
        """Copy all active account balances from one month to the next.

        Args:
            source_month (Month): Month to copy balances from.
            target_month (Month): Month to copy balances to.

        Returns:
            bool: True if copy was successful, False otherwise.
        """
        with self._uow() as uow:
            row_count = uow.balances.copy_by_month(source_month, target_month)
            if row_count == 0:
                logger.warning("No balances were copied.  Rolling back.")
                uow.rollback()
                return False
        return True

    def _select_month(self, n_months: int = 3) -> Month | None:
        """Select a month from recent months or input a specific month.

        Args:
            n_months: Number of recent months to display

        Returns:
            Selected Month object or None if quit
        """
        balance_counts = self._fetcher.get_balance_count_per_month()
        balance_counts.sort(key=lambda x: x[0], reverse=True)
        return self._presenter.select_month(balance_counts[:n_months])


def main() -> int:
    """Main entry point for roll balances forward CLI.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    from dotenv import load_dotenv

    from nwtrack.bootstrap.composition import Lifetime, build_base_sqlite_uow_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.balance_presenters import (
        RichBalancesRollForwardPresenter,
    )
    from nwtrack.entrypoints.cli.ui.factory import (
        Console,
        ConsoleFactory,
        ConsoleSettings,
    )

    load_dotenv()
    setup_logging()

    console_default = ConsoleSettings(record=False)

    container = build_base_sqlite_uow_container()
    container.register(
        Console,
        lambda _: ConsoleFactory(console_default)(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        BalancesRollForwardPresenter,
        lambda c: RichBalancesRollForwardPresenter(console=c.resolve(Console)),
    ).register(
        RollBalancesUpdater,
        lambda c: RollBalancesUpdater(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(BalancesRollForwardPresenter),
        ),
    )
    result: OperationResult = container.resolve(RollBalancesUpdater).run()

    return 0 if result.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
