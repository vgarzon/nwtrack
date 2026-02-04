"""
Rich-based presenters for report-related use cases.
"""

from rich.console import Console
from rich.prompt import IntPrompt, Prompt

from nwtrack.application.dto import MonthlyCategoryBalance
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Balance, Category, NetWorth
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.renderers import (
    build_accounts_table,
    build_balances_table,
    build_category_summary_table,
    build_month_balances_table,
    build_networth_history_table,
    build_networth_history_total_change_table,
    build_networth_table,
)


class RichNetworthHistoryPresenter:
    """Rich-based implementation of NetworthHistoryPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def show_header(self) -> None:
        """Display report header using Rich."""
        self._console.rule("[bold green]Networth History Report", align="center")

    def display_networth_history(
        self, networth_records: list[NetWorth], currency_code: str
    ) -> None:
        """Display networth history table using Rich.

        Args:
            networth_records: List of networth records to display
            currency_code: Currency code for the report
        """
        table = build_networth_history_table(networth_records)
        self._console.print(table)

    def show_no_data_warning(self, currency_code: str) -> None:
        """Display warning when no data is found.

        Args:
            currency_code: Currency code that was searched
        """
        self._console.print(f"[red]No net worth data found in {currency_code}[/red]")

    def show_partial_data_warning(
        self, requested: int, found: int, currency_code: str
    ) -> None:
        """Display warning when fewer records than requested are found.

        Args:
            requested: Number of months requested
            found: Number of months actually found
            currency_code: Currency code for the report
        """
        self._console.print(
            f"[yellow]Only {found} months of net worth data found in "
            f"{currency_code}[/yellow]"
        )

    def display_total_change(
        self, networth_records: list[NetWorth], currency_code: str
    ) -> None:
        """Display total change in net worth over the period.

        Args:
            networth_records: List of networth records
            currency_code: Currency code for the report
        """
        if len(networth_records) < 2:
            return

        def calc_change(xa, xb, attr):
            """Calculate absolute and percentage change in attribute."""
            a = getattr(xa, attr)
            b = getattr(xb, attr)
            return b - a, (b - a) / a if a != 0 else 0

        changes = {
            k: calc_change(networth_records[0], networth_records[-1], k)
            for k in ["assets", "liabilities", "net_worth"]
        }
        table = build_networth_history_total_change_table(changes)
        self._console.print(table)


class RichBalancesByCategoryPresenter:
    """Rich-based implementation of BalancesByCategoryPresenter."""

    def __init__(self, fetcher: FetchService, console: Console) -> None:
        self._fetcher = fetcher
        self._console = console
        self._prompt = Prompt(console=console)
        self._int_prompt = IntPrompt(console=console)

    def show_header(self) -> None:
        """Display report header using Rich."""
        self._console.rule("[bold green]Balance Summary by Category", align="center")

    def show_accounts_table(
        self,
        accounts: list[Account],
        category_map: dict[int, Category | None],
        title_prefix: str = "",
    ) -> None:
        """Show active accounts."""
        table = build_accounts_table(accounts, category_map, title_prefix)
        self._console.print(table)

    def show_balances_table(
        self,
        balances: list[Balance],
        account_map: dict[int, Account],
        category_map: dict[int, Category | None],
        title_suffix: str = "",
    ) -> None:
        """Show balances table with account and category information.

        Args:
            balances: List of balances
            account_map: Mapping of account IDs to Account objects
            category_map: Mapping of account IDs to Category objects
            title_suffix: Suffix for the table title

        Returns:
            None
        """
        table = build_balances_table(
            balances, account_map, category_map, title_suffix=title_suffix
        )
        self._console.print(table)

    def show_summary_by_category(
        self, monthly_balances: list[MonthlyCategoryBalance], title_suffix: str = ""
    ) -> None:
        """Print summary by category for a specific month.

        Args:
            monthly_balances: list[MonthlyCategoryBalance]
            title_suffix: Suffix for the table title
        """
        table = build_category_summary_table(
            monthly_balances, title_suffix=title_suffix
        )
        self._console.print(table)

    def show_networth_table(
        self, nw: NetWorth, title_suffix: str = "", form: str = "wide"
    ) -> None:
        """Print net worth on a specific month.

        Args:
            nw (NetWorth): NetWorth object
            title_suffix (str): Suffix for the table title
            form (str): Table form, either "wide" or "long"

        Returns:
            None
        """
        table = build_networth_table(nw, title_suffix, form=form)
        self._console.print(table)

    def prompt_for_month_choice(
        self, balance_counts: list[tuple[Month, int]]
    ) -> Month | None:
        """Present month selection with recent months or custom input.

        Args:
            balance_counts: List of (Month, count) tuples for recent months

        Returns:
            Selected Month or None if cancelled
        """
        recent_months = [month for month, _ in balance_counts]
        n_months = len(balance_counts)

        table = build_month_balances_table(balance_counts)
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
            return self._input_custom_month()

        choice_idx = int(choice) - 1
        return recent_months[choice_idx]

    def _input_custom_month(self) -> Month | None:
        """Input a specific month from user."""
        from datetime import date

        today = date.today()
        _year = self._int_prompt.ask("Enter year as 'YYYY'", default=today.year)
        _month = self._int_prompt.ask("Enter month as 'MM'", default=today.month)

        try:
            month = Month(year=_year, month=_month)
        except ValueError:
            self.show_invalid_month_error()
            return None

        if not self._fetcher.check_month_in_balances(month):
            self.show_no_balances_warning(month)
            return None

        return month

    def show_invalid_month_error(self) -> None:
        """Display error for invalid month input."""
        self._console.print("[red]Invalid month format. Please use YYYY-MM.[/red]")

    def show_no_balances_warning(self, month: Month) -> None:
        """Display warning when no balances found for month.

        Args:
            month: The month that has no balances
        """
        self._console.print(f"[orange3]No balance entries found in {month}.[/orange3]")

    def show_no_month_selected_message(self) -> None:
        """Display messag3 when no month is selected."""
        self._console.print("[orange3]No month selected. Exiting report.[/orange3]")

    def show_no_networth_data_warning(self, month: Month, currency_code: str) -> None:
        """Display warning when no net worth data found for month and currency.

        Args:
            month: The month that has no net worth data
            currency_code: The currency code that was searched
        """
        self._console.print(
            f"[red]No net worth data found for {month} in {currency_code}[/red]"
        )
