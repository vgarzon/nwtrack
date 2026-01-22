"""
Print network summary by category
"""

import logging
from typing import Callable

from rich.console import Console
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from nwtrack.application.dto import MonthlyCategoryBalance
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.domain.models import Account, Balance, Category, NetWorth
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class SummaryService:
    """Print net worth summary by category."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow
        self._console = Console()

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
        balance_counts = self._get_balance_count_per_month()
        balance_counts.sort(key=lambda x: x[0], reverse=True)
        recent_months = [month for month, _ in balance_counts[:n_months]]
        table = self._build_month_balances_table(balance_counts[:n_months])
        self._console.print(table)
        self._console.print("Options:")
        self._console.print("  [bold]A.[/bold] Enter year and month")
        self._console.print("  [bold]Q.[/bold] Quit")
        choice = Prompt.ask(
            "[bold]Enter choice[/bold]",
            choices=[str(i + 1) for i in range(n_months)] + ["A", "Q"],
            default="1",
            case_sensitive=False,
        )
        if choice.lower().strip() == "q":
            return None
        if choice.lower().strip() == "a":
            return self.input_month()
        choice_idx = int(choice) - 1
        return recent_months[choice_idx]

    def input_month(self) -> Month | None:
        """Input a specific month from user.

        Returns:
            Month | None: Month object or None if quit
        """
        from datetime import date

        today = date.today()
        _year = IntPrompt.ask("Enter year as 'YYYY'", default=today.year)
        _month = IntPrompt.ask("Enter month as 'MM'", default=today.month)
        try:
            month = Month(year=_year, month=_month)
        except ValueError:
            logger.error("Invalid Month inputs %d %d", _year, _month)
            self._console.print("[red]Invalid month format. Please use YYYY-MM.[/red]")
            return None
        with self._uow() as uow:
            if not uow.balances.check_month(month):
                logger.warning(f"No balance entries found for {month}.")
                self._console.print(
                    f"[orange]No balance entries found in {month}.[/orange]"
                )
                return None
        return month

    def print_active_accounts(self):
        """Print active accounts."""
        active_accounts = self._get_active_accounts()
        table = self._build_accounts_table(active_accounts)
        self._console.print(table)

    def print_balances(self, month: Month):
        """Print balances for a specific month.

        Args:
            month (Month): Month object

        Returns:
            None
        """
        balances = self._get_month_balances(month, active_only=True)
        table = self._build_balances_table(balances, title_suffix=str(month))
        self._console.print(table)

    def print_summary_by_category(self, month: Month) -> None:
        """Print summary by category for a specific month.
        Args:
            month (Month): Month object
        Returns:
            None
        """
        with self._uow() as uow:
            monthly_balances = uow._reporting.monthly_balance_total_by_category(month)
        table = self._build_category_summary_table(
            monthly_balances, title_suffix=str(month)
        )
        self._console.print(table)

    def print_net_worth(self, month: Month, currency_code: str = "USD") -> None:
        """Print net worth on a specific month.

        Args:
            month (Month): Month object
            currency (str): Currency code (default: "USD")

        Returns:
            None
        """
        with self._uow() as uow:
            nw = uow.net_worth.get(month, currency_code)
        if not nw:
            logger.warning("No net worth data found for %s in %s", month, currency_code)
            self._console.print(
                f"[red]No net worth data found for {month} in {currency_code}[/red]"
            )
            return
        title_suffix = f"{month} ({currency_code})"
        table = self._build_networth_table(nw, title_suffix, form="wide")
        self._console.print(table)

    def _build_networth_table(
        self, nw: NetWorth, title_suffix: str = "", form="wide"
    ) -> Table:
        """Build a Rich Table of net worth summary.

        Args:
            month (Month): Month object
            title_suffix (str): Suffix for table title
            form (str): Table format, "wide" or "long"
        Returns:
            Table: Rich Table object
        """
        _title = "Net Worth Summary" + (f" {title_suffix}" if title_suffix else "")
        table = Table(title=_title)
        if form == "long":
            table.add_column("Side", style="magenta")
            table.add_column("Total", justify="right", style="red")
            table.add_row("Assets", f"{nw.assets:9,}")
            table.add_row("Liabilities", f"{nw.liabilities:9,}")
            table.add_row("Net Worth", f"{nw.net_worth:9,}")
        elif form == "wide":
            table.add_column("Assets", justify="right", style="green")
            table.add_column("Liabilities", justify="right", style="yellow")
            table.add_column("Net Worth", justify="right", style="red")
            table.add_row(
                f"{nw.assets:9,}",
                f"{nw.liabilities:9,}",
                f"{nw.net_worth:9,}",
            )
        else:
            logger.error("Invalid table form: %s", form)
            raise ValueError(f"Invalid table form: {form}")
            table = Table()
        return table

    def _build_accounts_table(self, accounts: list[Account]) -> Table:
        """Build a Rich Table of active accounts.
        Args:
            accounts (list[Account]): List of Account objects
        Returns:
            Table: Rich Table object
        """
        table = Table(title="Active Accounts")
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Category", style="green")
        table.add_column("Side", style="yellow")
        for account in accounts:
            category = self._get_category_by_account_id(account.id)
            category_name = category.name if category else "Unknown"
            side = category.side.value if category else "Unknown"
            table.add_row(
                str(account.id),
                account.name,
                category_name,
                side,
            )
        return table

    def _build_month_balances_table(
        self, balance_counts: list[tuple[Month, int]]
    ) -> Table:
        """Build a Rich Table of balances per month.

        Args:
            balance_counts (list[tuple[Month, int]]): List of tuples Month and count of balances
        Returns:
            Table: Rich Table object
                idx (starts at 1) | month | count
        """
        table = Table(title="Balance Entries per Month")
        table.add_column("Index", justify="right", style="green")
        table.add_column("Month", style="cyan")
        table.add_column("Balances", justify="right", style="magenta")
        for idx, (month, count) in enumerate(balance_counts):
            table.add_row(str(idx + 1), str(month), str(count))
        return table

    def _build_balances_table(
        self, balances: list[Balance], title_suffix: str = ""
    ) -> Table:
        """Build a Rich Table of balances.

        Args:
            balances (list[Balance]): List of Balance objects
            title_suffix (str): Suffix for table title
        Returns:
            Table: Rich Table object
        """
        account_map = self._get_map_id_to_account()
        _title = "Balances" + (f" {title_suffix}" if title_suffix else "")
        table = Table(title=_title)
        table.add_column("Acct_ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Account Name", style="magenta")
        table.add_column("Category", style="green")
        table.add_column("Side", style="yellow")
        table.add_column("Amount", justify="right", style="red")
        for balance in balances:
            account_id = balance.account_id
            account_name = account_map[account_id].name
            category = self._get_category_by_account_id(account_id)
            if not category:
                logger.error("Category not found for account ID {%}", account_id)
            category_name = category.name if category else "Unknown"
            side = category.side.value if category else "Unknown"
            table.add_row(
                str(account_id),
                account_name,
                category_name,
                side,
                f"{balance.amount:8,}",
            )
        return table

    def _build_category_summary_table(
        self, monthly_balances: list[MonthlyCategoryBalance], title_suffix: str = ""
    ) -> Table:
        """Build a Rich Table of summary by category.

        Args:
            monthly_balances: List of MonthlyCategoryBalance objects
            title_suffix (str): Suffix for table title

        Returns:
            Table: Rich Table object
        """
        _title = "Summary by Category" + (f" {title_suffix}" if title_suffix else "")
        table = Table(title=_title)
        table.add_column("Category", style="magenta")
        table.add_column("Side", style="green")
        table.add_column("Total", justify="right", style="red")
        for mb in monthly_balances:
            category_name = mb.category.name
            category_side = mb.category.side.value
            amount = mb.amount
            table.add_row(
                category_name,
                category_side,
                f"{amount:8,}",
            )
        return table

    def _get_category_by_account_id(self, account_id: int) -> Category | None:
        """Get category side for a given account ID.

        Args:
            account_id (int): Account ID

        Returns:
            Category | None: Category instance if found, else None.
        """
        with self._uow() as uow:
            account = uow.accounts.get_by_id(account_id)
        if not account:
            return None
        with self._uow() as uow:
            category = uow.categories.get(account.category_name)
        return category

    def _get_map_id_to_account(self) -> dict[int, Account]:
        """Get a map of account id to Account objects.

        Returns:
            dict[int, Account]: Map of account id to Account objects.
        """
        with self._uow() as uow:
            accounts = uow.accounts.get_all()
        return {acc.id: acc for acc in accounts}

    def _get_balance_count_per_month(self) -> list[tuple[Month, int]]:
        """Get count of balance entries per month.

        Returns:
            list[tuple[Month, int]]: list of tuples Month count of balance entries.
        """
        with self._uow() as uow:
            counts = uow.balances.count_per_month()
        return counts

    def _get_active_accounts(self) -> list[Account]:
        """Get list of active accounts.

        Returns:
            list[Account]: List of active Account objects.
        """
        with self._uow() as uow:
            accounts = uow.accounts.get_active()
        return accounts

    def _get_month_balances(
        self, month: Month, active_only: bool = True
    ) -> list[Balance]:
        """Get balance all accounts on a specific month.

        Args:
            month (Month): Month object
            active_only (bool): Whether to include only active accounts

        Return:
            list[Balance]: List of Balance object for the specified account and month.
        """
        with self._uow() as uow:
            balances = uow.balances.get_month(month, active_only)
        return balances


def main() -> None:
    from dotenv import load_dotenv

    from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
    from nwtrack.bootstrap.logging_config import setup_logging

    load_dotenv()
    setup_logging()

    container = build_base_sqlite_uow_container()
    container.register(
        SummaryService,
        lambda c: SummaryService(uow=lambda: c.resolve(UnitOfWork)),
    )
    service: SummaryService = container.resolve(SummaryService)
    service.run()


if __name__ == "__main__":
    main()
