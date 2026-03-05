"""
Delete balance entry interactively.
"""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import BalanceDeleterPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class BalanceDeleter:
    """Delete balance entries interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        presenter: BalanceDeleterPresenter,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        """Main entry point for balance deletion."""
        logger.info("Starting Balance Deleter")
        self._presenter.show_header()

        month = self._select_month()
        if month is None:
            self._presenter.show_cancellation()
            logger.warning("No month selected. Exiting.")
            return OperationResult(success=False, error_message="No month selected.")
        if not self._fetcher.check_month_in_balances(month):
            self._presenter.show_no_balances_warning(month)
            logger.warning("No balances found for %s.  Stopping.", month)
            return OperationResult(
                success=False, error_message="No balances for selected month."
            )

        self.display_balances(month)

        account_id = self._presenter.select_account(month)
        if account_id is None:
            self._presenter.show_cancellation()
            logger.warning("No account selected. Exiting.")
            return OperationResult(success=False, error_message="No account selected.")

        try:
            balance = self._fetcher.get_balance_for_account_id(month, account_id)
        except (IndexError, ValueError):
            _msg = f"No balance found for account {account_id} on {month}."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        account = self._fetcher.get_account_by_id(account_id)
        if account is None:
            _msg = f"Account {account_id} not found."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        self._presenter.show_balance_details(account, balance, month)

        if not self._presenter.prompt_to_confirm_deletion():
            _msg = "Deletion cancelled by user."
            self._presenter.show_cancellation()
            logger.warning(_msg)
            return OperationResult(success=False, error_message=_msg)

        if not self.delete_balance(account_id, month):
            _msg = "Failed to delete balance."
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        self._presenter.show_success("Balance deleted successfully.")
        self.display_balances(month)

        logger.info("Finished Balance Deleter")
        return OperationResult(success=True)

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

    def delete_balance(self, account_id: int, month: Month) -> bool:
        """Delete balance entry in transaction.

        Args:
            account_id (int): Account ID
            month (Month): Month object

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._uow() as uow:
                rowcount = uow.balances.delete_by_account_and_month(account_id, month)
                if rowcount == 0:
                    logger.warning("No balance found to delete.")
                    uow.rollback()
                    return False
                elif rowcount > 1:
                    logger.error("Multiple balances deleted (unexpected).")
                    uow.rollback()
                    return False
            return True
        except Exception as e:
            logger.exception("Error deleting balance: %s", e)
            return False

    def display_balances(self, month: Month) -> None:
        """Display balance data for a given month.

        Args:
            month (Month): Month object
        """
        balances = self._fetcher.get_month_balances(month, active_only=True)
        account_map = self._fetcher.get_map_id_to_account()
        self._presenter.display_balances(balances, account_map, title_suffix=str(month))


def main() -> int:
    """Main entry point for balance deletion script.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    from dotenv import load_dotenv

    from nwtrack.bootstrap.composition import build_base_container
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.balance_presenters import (
        RichBalanceDeleterPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import Console, ConsoleSettings
    from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory

    load_dotenv()
    setup_logging()

    console_default = ConsoleSettings(record=False)

    container = build_base_container()
    container.register(
        Console,
        lambda _: ConsoleFactory(default_settings=console_default)(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        BalanceDeleterPresenter,
        lambda c: RichBalanceDeleterPresenter(console=c.resolve(Console)),
    ).register(
        BalanceDeleter,
        lambda c: BalanceDeleter(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(BalanceDeleterPresenter),
        ),
    )
    result: OperationResult = container.resolve(BalanceDeleter).run()

    return 0 if result.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
