"""
Update active account balances interactively
"""

import logging
from collections.abc import Callable

from rich.console import Console
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Balance, NetWorth
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class BalanceUpdater:
    """Update account balances interactively."""

    def __init__(
        self, uow: Callable[[], UnitOfWork], fetcher: FetchService, console: Console
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._console = console
        self._prompt = Prompt(console=self._console)
        self._int_prompt = IntPrompt(console=self._console)

    def run(self) -> None:
        logger.info("Starting Balance Updater")
        self._console.rule("[bold green]Balance Updater[/bold green]")
        self.print_active_accounts()
        month = self.select_month()
        if month is None:
            logger.warning("No month selected. Exiting.")
            self._console.print("[orange]No month selected. Exiting.[/orange]")
            return
        self.update_balances_loop(month)
        print("Final active account balances:")
        self.print_balances(month)
        self.print_net_worth(month)
        logger.info("Finished Balance Updater")

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
        table = self._build_month_balances_table(balance_counts[:n_months])
        self._console.print(table)
        self._console.print("Options:")
        self._console.print("  [bold]A.[/bold] Enter year and month")
        self._console.print("  [bold]Q.[/bold] Quit")
        choice = self._prompt.ask(
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
        _year = self._int_prompt.ask("Enter year as 'YYYY'", default=today.year)
        _month = self._int_prompt.ask("Enter month as 'MM'", default=today.month)
        try:
            month = Month(year=_year, month=_month)
        except ValueError:
            logger.error("Invalid Month inputs %d %d", _year, _month)
            self._console.print("[red]Invalid month format. Please use YYYY-MM.[/red]")
            return None

        if not self._fetcher.check_month_in_balances(month):
            logger.warning(f"No balance entries found for {month}.")
            self._console.print(
                f"[orange]No balance entries found in {month}.[/orange]"
            )
            return None
        return month

    def update_balances_loop(self, month: Month) -> None:
        while True:
            self.print_balances(month)
            res = self._prompt.ask("Enter account ID or 'q' to quit")
            if res.lower() == "q":
                break
            try:
                account_id = int(res)
            except ValueError:
                self._console.print(
                    "[magenta bold]Invalid input.[/magenta bold] "
                    "Please enter a valid account ID or 'q' to quit."
                )
                continue
            self.update_account_balance(account_id, month)

    def update_account_balance(self, account_id: int, month: Month) -> None:
        accounts_map_id = self._fetcher.get_map_id_to_account()
        balance = self._fetcher.get_balance_for_account_id(month, account_id)
        current_balance = balance.amount if balance else 0
        if account_id not in accounts_map_id:
            logger.error(f"Account id '{account_id}' not found")
            raise ValueError("Account id '%d' not found", account_id)
        _account: Account | None = accounts_map_id.get(account_id)
        assert _account is not None
        account_name: str = _account.name
        self._console.print(
            f"Account [bold]{account_name}[/bold] ({account_id}) balance on "
            f"{month}: [bold green]{current_balance:8,}[/bold green]"
        )
        new_amount = self._int_prompt.ask("Enter [bold]new balance[/bold] amount")
        self.update_balance(account_id, month, new_amount)

    def print_active_accounts(self):
        """Print active accounts."""
        active_accounts = self._fetcher.get_accounts(active_only=True)
        table = self._build_accounts_table(active_accounts)
        self._console.print(table)

    def _build_month_balances_table(
        self, balance_counts: list[tuple[Month, int]]
    ) -> Table:
        """Build a Rich Table of balances per month.

        Args:
            balance_counts: List of tuples (Month, count of balances)

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
            category = self._fetcher.get_category_by_account_id(account.id)
            category_name = category.name if category else "Unknown"
            side = category.side.value if category else "Unknown"
            table.add_row(
                str(account.id),
                account.name,
                category_name,
                side,
            )
        return table

    def print_balances(self, month: Month):
        """Print balances for a specific month.

        Args:
            month (Month): Month object

        Returns:
            None
        """
        balances = self._fetcher.get_month_balances(month, active_only=True)
        table = self._build_balances_table(balances, title_suffix=str(month))
        self._console.print(table)

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
        account_map = self._fetcher.get_map_id_to_account()
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
            category = self._fetcher.get_category_by_account_id(account_id)
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

    def update_balance(self, account_id: int, month: Month, new_amount: int) -> None:
        """Update the balance for a specific account on a given month.

        Args:
            account_id (int): ID of the account.
            month (Month): Month of the balance to update.
            new_ammount (int): New balance amount.
        """
        with self._uow() as uow:
            # TODO: handle return value / exceptions
            uow.balances.update(
                account_id=account_id, month=month, new_amount=new_amount
            )


def main() -> None:
    from dotenv import load_dotenv

    from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging

    load_dotenv()
    setup_logging()

    container = build_base_sqlite_uow_container()
    container.register(
        Console,
        lambda c: Console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        BalanceUpdater,
        lambda c: BalanceUpdater(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            console=c.resolve(Console),
        ),
    )
    container.resolve(BalanceUpdater).run()


if __name__ == "__main__":
    main()
