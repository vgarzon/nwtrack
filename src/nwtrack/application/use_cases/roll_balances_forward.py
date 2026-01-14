"""
Roll balances forward to next available month.
"""

import logging
from typing import Callable

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.domain.models import Balance, NetWorth
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class RollBalancesUpdater:
    """Update account balances interactively."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow
        self._console = Console()

    def run(self) -> None:
        logger.info("Starting Roll Balances Forward Updater")
        self._console.rule("[bold green]Roll Balances Forward[/bold green]")
        target_month = self._get_next_free_month()
        self._console.print(f"Next available target month: [bold]{target_month}[/bold]")
        proceed = Confirm.ask(
            f"Roll balances forward into [bold]{target_month}[/bold]?", default=True
        )
        if not proceed:
            self._console.print("[magenta]Stopping.[/magenta]")
            return
        source_month = self.select_month()
        if source_month is None:
            logger.info("User cancelled month selection.")
            self._console.print("[magenta]Stopping.[/magenta]")
            return
        logger.info(f"Rolling balances from {source_month} to {target_month}")
        self._copy_monthly_balances(source_month, target_month)
        self.print_net_worth(target_month)
        logger.info("Finished Roll Balances Forward Updater")

    def _get_next_free_month(self) -> Month:
        """Get the next month that does not have balances yet.

        Returns:
            Month: Next month without balances.
        """
        recent_months = self._get_sorted_recent_months()
        latest_month = recent_months[0]
        next_month = latest_month.increment()
        return next_month

    def _get_sorted_recent_months(self) -> list[Month]:
        """Get sorted recent months with balances.

        Returns:
            list[Month]: List of recent months in descending order.
        """
        balance_counts = self._get_balance_count_per_month()
        if not balance_counts:
            logger.error("No balances found in the system.")
            raise ValueError("No balances found in the system.")
        balance_counts.sort(key=lambda x: x[0], reverse=True)
        recent_months = [month for month, _ in balance_counts]
        return recent_months

    def _copy_monthly_balances(self, source_month: Month, target_month: Month) -> None:
        """Copy all active account balances from one month to the next.

        Args:
            source_month (Month): Month to copy balances from.
            target_month (Month): Month to copy balances to.
        """
        with self._uow() as uow:
            if not uow.balances.check_month(source_month):
                logger.error(f"No balances found for month {source_month}")
                raise ValueError(f"No balances found for month {source_month}")
        logger.info(f"Rolling balances forward from {source_month} to {target_month}.")
        self._console.print(
            f"[green]\nRolling balances forward [bold]from {source_month} to "
            f"{target_month}.[/bold][/green]\n"
        )
        with self._uow() as uow:
            row_count = uow.balances.copy_by_month(source_month, target_month)
            if row_count == 0:
                logger.warning("No balances were copied.  Rolling back.")
                self._console.print(
                    "[magenta]No balances were copied.  Rolling back.[/magenta]"
                )
                uow.rollback()

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
        self._console.print("Other options:")
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
            raise ValueError(f"No net worth data found for {month} in {currency_code}")
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
        table = Table(title="Source Months with Balances")
        table.add_column("Index", justify="right", style="green")
        table.add_column("Month", style="cyan")
        table.add_column("Balances", justify="right", style="magenta")
        for idx, (month, count) in enumerate(balance_counts):
            table.add_row(str(idx + 1), str(month), str(count))
        return table

    def _get_balance_count_per_month(self) -> list[tuple[Month, int]]:
        """Get count of balance entries per month.

        Returns:
            list[tuple[Month, int]]: list of tuples Month count of balance entries.
        """
        with self._uow() as uow:
            counts = uow.balances.count_per_month()
        return counts

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
        RollBalancesUpdater,
        lambda c: RollBalancesUpdater(uow=lambda: c.resolve(UnitOfWork)),
    )
    updater: RollBalancesUpdater = container.resolve(RollBalancesUpdater)
    updater.run()


if __name__ == "__main__":
    main()
