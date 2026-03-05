"""
Update active account balances interactively
"""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import BalanceUpdatePresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import NetWorth
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class BalanceUpdater:
    """Update account balances interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        presenter: BalanceUpdatePresenter,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        """Run the balance update workflow.

        Returns:
            OperationResult indicating success/failure
        """
        logger.info("Starting Balance Updater")

        # Show header and active accounts
        self._presenter.show_header()
        self._display_active_accounts()

        # Select month
        month = self._select_month()
        if month is None:
            logger.warning("No month selected. Exiting.")
            self._presenter.show_no_month_selected()
            return OperationResult(success=False, error_message="No month selected")
        if not self._fetcher.check_month_in_balances(month):
            self._presenter.show_no_balances_warning(month)
            logger.warning("No balances found for %s.  Stopping.", month)
            return OperationResult(
                success=False, error_message="No balances for selected month."
            )

        # Interactive update loop
        self._run_update_loop(month)

        # Display final summary
        networth = self._fetcher.get_networth(month, "USD")
        self._display_final_summary(networth, month)

        logger.info("Finished Balance Updater")
        return OperationResult(success=True)

    def _display_active_accounts(self) -> None:
        """Display a list of active accounts."""
        active_accounts = self._fetcher.get_accounts(active_only=True)
        self._presenter.display_active_accounts(active_accounts)

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

    def _run_update_loop(self, month: Month) -> None:
        """Run interactive loop for updating balances.

        Args:
            month: Month for which to update balances
        """
        while True:
            # Display current balances
            self._display_balances(month)

            # Prompt for account ID
            account_id = self._presenter.prompt_for_account_id()
            if account_id is None:
                break  # User wants to quit
            if account_id == -1:
                continue  # Invalid input, try again

            # Update the balance for selected account
            try:
                self._update_single_balance(account_id, month)
            except ValueError as e:
                logger.error("Error updating balance: %s", e)
                continue

    def _display_balances(self, month: Month) -> None:
        """Display balances to select from.

        Args:
            month (Month): Month object
        """
        balances = self._fetcher.get_month_balances(month, active_only=True)
        self._presenter.display_balances(balances, month)

    def _update_single_balance(self, account_id: int, month: Month) -> None:
        """Update balance for a single account.

        Args:
            account_id: ID of the account to update
            month: Month of the balance to update

        Raises:
            ValueError: If account ID is not found
        """
        # Get account info
        account = self._fetcher.get_account_by_id(account_id)
        if account is None:
            logger.error(f"Account id '{account_id}' not found")
            raise ValueError(f"Account id '{account_id}' not found")

        # Get current balance
        balance = self._fetcher.get_balance_for_account_id(month, account_id)
        current_balance = balance.amount if balance else 0

        # Prompt for new amount
        new_amount = self._presenter.show_current_balance_and_prompt(
            account.name, account_id, month, current_balance
        )

        # Update in database
        with self._uow() as uow:
            uow.balances.update(
                account_id=account_id, month=month, new_amount=new_amount
            )

    def _display_final_summary(self, networth: NetWorth | None, month: Month) -> None:
        """Display final balances and net worth summary.

        Args:
            balances: Final list of balances
            networth: Net worth data or None if not available
            month: Month for the summary
        """
        self._display_balances(month)
        if networth:
            self._presenter.display_networth(networth, month)


def main() -> int:
    """Main entry point for balance update script.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.bootstrap.composition import build_base_container
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.balance_presenters import (
        RichBalanceUpdatePresenter,
    )

    load_dotenv()
    setup_logging()

    container = build_base_container()
    container.register(
        Console,
        lambda _: Console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichBalanceUpdatePresenter,
        lambda c: RichBalanceUpdatePresenter(console=c.resolve(Console)),
    ).register(
        BalanceUpdater,
        lambda c: BalanceUpdater(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(RichBalanceUpdatePresenter),
        ),
    )

    result: OperationResult[None] = container.resolve(BalanceUpdater).run()

    return 0 if result.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
