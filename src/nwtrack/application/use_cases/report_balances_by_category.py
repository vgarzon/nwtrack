"""
Print summary of balances by category.
"""

import logging

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Category
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory
from nwtrack.entrypoints.cli.ui.prompts import prompt_for_month, prompt_for_month_choice
from nwtrack.entrypoints.cli.ui.renderers import (
    build_accounts_table,
    build_balances_table,
    build_category_summary_table,
    build_networth_table,
)

logger = logging.getLogger(__name__)


class ReportBalancesByCategory:
    """Print summary of balances by category."""

    def __init__(self, fetcher: FetchService, console_factory: ConsoleFactory) -> None:
        self._fetcher = fetcher
        self._console = console_factory()

    def run(self) -> None:
        """Run the summary service."""
        logger.info("Starting Print Summary Service")
        self._console.rule("[bold green]Balance Summary by Category", align="center")
        self.print_active_accounts()
        month = self.select_month()
        if month is None:
            logger.warning("No month selected. Exiting.")
            self._console.print("[orange]No month selected. Exiting.[/orange]")
            return
        self.print_balances(month)
        self.print_summary_by_category(month)
        self.print_net_worth(month)
        logger.info("Finished Print Summary Service")

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

    def print_active_accounts(self) -> None:
        """Print active accounts."""
        accounts, category_map = self._fetch_account_data(active_only=True)
        title_prefix = "Active"
        table = build_accounts_table(accounts, category_map, title_prefix)
        self._console.print(table)

    def print_balances(self, month: Month):
        """Print balances for a specific month.

        Args:
            month (Month): Month object

        Returns:
            None
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

    def print_summary_by_category(self, month: Month) -> None:
        """Print summary by category for a specific month.
        Args:
            month (Month): Month object
        Returns:
            None
        """
        monthly_balances = self._fetcher.get_monthly_balance_total_by_category(month)
        table = build_category_summary_table(monthly_balances, title_suffix=str(month))
        self._console.print(table)

    def print_net_worth(self, month: Month, currency_code: str = "USD") -> None:
        """Print net worth on a specific month.

        Args:
            month (Month): Month object
            currency (str): Currency code (default: "USD")

        Returns:
            None
        """
        nw = self._fetcher.get_networth(month, currency_code)
        if not nw:
            logger.warning("No net worth data found for %s in %s", month, currency_code)
            self._console.print(
                f"[red]No net worth data found for {month} in {currency_code}[/red]"
            )
            return
        title_suffix = f"{month} ({currency_code})"
        try:
            table = build_networth_table(nw, title_suffix, form="wide")
        except ValueError as e:
            logger.error("Error building net worth table: %s", e)
            self._console.print(f"[red]Error building net worth table: {e}[/red]")
            return
        self._console.print(table)

    def _fetch_account_data(
        self, active_only: bool = True
    ) -> tuple[list[Account], dict[int, Category | None]]:
        """Build the accounts table.

        Args:
            active_only (bool): Whether to print only active accounts.

        Returns:
            tuple[list[Account], dict[int, Category]]: List of accounts and
                mapping of account IDs to categories.
        """
        accounts = self._fetcher.get_accounts(active_only=active_only)
        categories_map = {
            account.id: self._fetcher.get_category_by_account_id(account.id)
            for account in accounts
        }
        return accounts, categories_map


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
        ReportBalancesByCategory,
        lambda c: ReportBalancesByCategory(
            fetcher=c.resolve(FetchService),
            console_factory=c.resolve(ConsoleFactory),
        ),
    )
    container.resolve(ReportBalancesByCategory).run()


if __name__ == "__main__":
    main()
