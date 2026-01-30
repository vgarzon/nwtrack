"""
Delete balance entry interactively.
"""

import logging
from collections.abc import Callable

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Category
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory
from nwtrack.entrypoints.cli.ui.prompts import (
    prompt_for_account_id,
    prompt_for_month,
    prompt_for_month_choice,
    prompt_to_confirm_action,
)
from nwtrack.entrypoints.cli.ui.renderers import (
    build_accounts_table,
    build_balances_table,
)

logger = logging.getLogger(__name__)


class BalanceDeleter:
    """Delete balance entries interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        console_factory: ConsoleFactory,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._console = console_factory()

    def run(self) -> None:
        """Main entry point for balance deletion."""
        logger.info("Starting Balance Deleter")
        self._console.rule("[bold red]Balance Deletion[/bold red]")

        # Show active accounts
        self.print_active_accounts()

        # Select month
        month = self.select_month()
        if month is None:
            logger.warning("No month selected. Exiting.")
            self._console.print("[orange]No month selected. Exiting.[/orange]")
            return

        # Show balances for selected month
        self.print_balances(month)

        # Select account
        account_id = self.select_account(month)
        if account_id is None:
            logger.warning("No account selected. Exiting.")
            self._console.print("[orange]Operation cancelled.[/orange]")
            return

        # Get balance for confirmation
        try:
            balance = self._fetcher.get_balance_for_account_id(month, account_id)
        except (IndexError, ValueError):
            _msg = f"No balance found for account {account_id} on {month}."
            logger.error(_msg)
            self._console.print(f"[red]{_msg}[/red]")
            return

        # Get account details for display
        account = self._fetcher.get_account_by_id(account_id)
        if account is None:
            _msg = f"Account {account_id} not found."
            logger.error(_msg)
            self._console.print(f"[red]{_msg}[/red]")
            return

        # Show balance details and confirm
        self._console.print("\n[bold]Balance to delete:[/bold]")
        self._console.print(f"  Account: {account.name} (ID: {account_id})")
        self._console.print(f"  Month: {month}")
        self._console.print(f"  Amount: {balance.amount:,}")

        if not prompt_to_confirm_action(self._console, "Delete this balance?"):
            logger.info("Deletion cancelled by user.")
            self._console.print("[orange]Deletion cancelled.[/orange]")
            return

        # Perform deletion
        success = self.delete_balance(account_id, month)
        if success:
            self._console.print(
                "[bold green]Balance deleted successfully.[/bold green]"
            )
            # Show updated balances
            self.print_balances(month)
        else:
            self._console.print("[bold red]Failed to delete balance.[/bold red]")

        logger.info("Finished Balance Deleter")

    def select_month(self, n_months: int = 3) -> Month | None:
        """Select a month from recent months or input a specific month.

        Args:
            n_months (int): Number of recent months to display

        Returns:
            Month | None: Selected Month object or None if quit
        """
        balance_counts = self._fetcher.get_balance_count_per_month()
        balance_counts.sort(key=lambda x: x[0], reverse=True)
        recent_months = [month for month, _ in balance_counts[:n_months]]
        choice = prompt_for_month_choice(self._console, balance_counts[:n_months])
        if choice == "q":
            return None
        if choice == "a":
            return self.input_month()
        choice_idx = int(choice) - 1
        return recent_months[choice_idx]

    def input_month(self) -> Month | None:
        """Input a specific month from user.

        Returns:
            Month | None: Month object or None if quit
        """
        while True:
            month = prompt_for_month(self._console)
            if month is None:
                return None
            if not self._fetcher.check_month_in_balances(month):
                _msg = f"No balance entries found for {month}."
                logger.warning(_msg)
                self._console.print(f"[orange]{_msg}[/orange]")
                continue
            break
        return month

    def select_account(self, month: Month) -> int | None:
        """Prompt for account ID and validate it exists.

        Args:
            month (Month): Month for context

        Returns:
            int | None: Account ID or None if user quits
        """
        account_id = prompt_for_account_id(self._console)
        return account_id

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

    def print_active_accounts(self) -> None:
        """Print active accounts table."""
        accounts, category_map = self._fetch_account_data(active_only=True)
        title_prefix = "Active"
        table = build_accounts_table(accounts, category_map, title_prefix)
        self._console.print(table)

    def print_balances(self, month: Month) -> None:
        """Print balances for a specific month.

        Args:
            month (Month): Month object
        """
        balances = self._fetcher.get_month_balances(month, active_only=True)
        account_map = self._fetcher.get_map_id_to_account()
        category_map = {
            b.account_id: self._fetcher.get_category_by_account_id(b.account_id)
            for b in balances
        }
        table = build_balances_table(
            balances, account_map, category_map, title_suffix=str(month)
        )
        self._console.print(table)

    def _fetch_account_data(
        self, active_only: bool = False
    ) -> tuple[list[Account], dict[int, Category | None]]:
        """Fetch accounts and category map.

        Args:
            active_only (bool): If True, fetch only active accounts

        Returns:
            tuple[list[Account], dict[int, Category | None]]: Accounts and category map
        """
        accounts = self._fetcher.get_accounts(active_only=active_only)
        category_map = {
            account.id: self._fetcher.get_category_by_account_id(account.id)
            for account in accounts
        }
        return accounts, category_map


def main() -> None:
    from dotenv import load_dotenv

    from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings

    load_dotenv()
    setup_logging()

    console_defaults = ConsoleSettings(record=False)

    container = build_base_sqlite_uow_container()
    container.register(
        ConsoleFactory,
        lambda _: ConsoleFactory(default_settings=console_defaults),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        BalanceDeleter,
        lambda c: BalanceDeleter(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            console_factory=c.resolve(ConsoleFactory),
        ),
    )
    container.resolve(BalanceDeleter).run()


if __name__ == "__main__":
    main()
