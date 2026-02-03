"""
Rich-based presenters for balance-related use cases.
"""

from datetime import date

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Balance, NetWorth
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.renderers import (
    build_month_balances_table,
    build_networth_table,
)


class RichBalanceUpdatePresenter:
    """Rich-based implementation of BalanceUpdatePresenter."""

    def __init__(self, console: Console, fetcher: FetchService) -> None:
        self._console = console
        self._fetcher = fetcher
        self._prompt = Prompt(console=self._console)
        self._int_prompt = IntPrompt(console=self._console)

    def show_header(self) -> None:
        """Display workflow header using Rich."""
        self._console.rule("[bold green]Balance Updater[/bold green]")

    def display_active_accounts(self, accounts: list[Account]) -> None:
        """Display active accounts table.

        Args:
            accounts: List of active accounts to display
        """
        table = self._build_accounts_table(accounts)
        self._console.print(table)

    def _build_accounts_table(self, accounts: list[Account]) -> Table:
        """Build Rich table of active accounts."""
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

    def select_month(self, balance_counts: list[tuple[Month, int]]) -> Month | None:
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
        self._console.print(f"[orange]No balance entries found in {month}.[/orange]")

    def show_no_month_selected(self) -> None:
        """Display message when no month is selected."""
        self._console.print("[orange]No month selected. Exiting.[/orange]")

    def display_balances(self, balances: list[Balance], month: Month) -> None:
        """Display balances table for a specific month.

        Args:
            balances: List of balances to display
            month: Month for the balances
        """
        table = self._build_balances_table(balances, title_suffix=str(month))
        self._console.print(table)

    def _build_balances_table(
        self, balances: list[Balance], title_suffix: str = ""
    ) -> Table:
        """Build Rich table of balances."""
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

    def prompt_for_account_id(self) -> int | None:
        """Prompt for account ID to update.

        Returns:
            Account ID or None if user wants to quit the loop
        """
        res = self._prompt.ask("Enter account ID or 'q' to quit")
        if res.lower() == "q":
            return None
        try:
            return int(res)
        except ValueError:
            self.show_invalid_account_id()
            return -1  # Signal invalid input (will be caught by use case)

    def show_invalid_account_id(self) -> None:
        """Display error for invalid account ID input."""
        self._console.print(
            "[magenta bold]Invalid input.[/magenta bold] "
            "Please enter a valid account ID or 'q' to quit."
        )

    def show_current_balance_and_prompt(
        self, account_name: str, account_id: int, month: Month, current_balance: int
    ) -> int:
        """Show current balance and prompt for new amount.

        Args:
            account_name: Name of the account
            account_id: ID of the account
            month: Month of the balance
            current_balance: Current balance amount

        Returns:
            New balance amount
        """
        self._console.print(
            f"Account [bold]{account_name}[/bold] ({account_id}) balance on "
            f"{month}: [bold green]{current_balance:8,}[/bold green]"
        )
        return self._int_prompt.ask("Enter [bold]new balance[/bold] amount")

    def display_final_summary(
        self, balances: list[Balance], networth: NetWorth | None, month: Month
    ) -> None:
        """Display final balances and net worth summary.

        Args:
            balances: Final list of balances
            networth: Net worth data or None if not available
            month: Month for the summary
        """
        print("Final active account balances:")
        self.display_balances(balances, month)

        if networth:
            self._display_networth(networth, month)

    def _display_networth(self, nw: NetWorth, month: Month) -> None:
        """Display net worth table."""
        currency_code = "USD"  # Hardcoded for now
        title_suffix = f"{month} ({currency_code})"
        table = build_networth_table(nw, title_suffix, form="wide")
        self._console.print(table)


class RichBalancesRollForwardPresenter:
    """Rich-based implementation of BalancesRollForwardPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console
        self._confirm = Confirm(console=self._console)
        self._prompt = Prompt(console=self._console)
        self._int_prompt = IntPrompt(console=self._console)

    def show_header(self) -> None:
        """Display workflow header using Rich."""
        self._console.rule("[bold green]Roll Balances Forward[/bold green]")

    def select_month(self, balance_counts: list[tuple[Month, int]]) -> Month | None:
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
        today = date.today()
        _year = self._int_prompt.ask("Enter year as 'YYYY'", default=today.year)
        _month = self._int_prompt.ask("Enter month as 'MM'", default=today.month)

        try:
            month = Month(year=_year, month=_month)
        except ValueError:
            self.show_invalid_month_error()
            return None

        # TODO: Re-enable month check when fetcher is available
        # if not self._fetcher.check_month_in_balances(month):
        #     self.show_no_balances_warning(month)
        #     return None

        return month

    def show_invalid_month_error(self) -> None:
        """Display error for invalid month input."""
        self._console.print("[red]Invalid month format. Please use YYYY-MM.[/red]")

    def confirm_target_month(self, target_month: Month) -> bool:
        """Prompt user to confirm rolling balances forward.

        Args:
            target_month: The month to roll balances into

        Returns:
            True if user confirms, False otherwise
        """
        self._console.print(f"Next available target month: [bold]{target_month}[/bold]")
        answer = self._confirm.ask(
            f"Roll balances forward into [bold]{target_month}[/bold]?", default=True
        )
        return answer

    def prompt_to_confirm_months(
        self, source_month: Month, target_month: Month
    ) -> bool:
        """Prompt user to confirm continuation.

        Args:
            source_month: The month to copy balances from
            target_month: The month to copy balances to

        Returns:
            True if user confirms, False otherwise
        """
        return self._confirm.ask(
            f"Copy balances from [bold]{source_month}[/bold] to "
            f"[bold]{target_month}[/bold]?",
            default=False,
        )

    def show_cancellation(self) -> None:
        """Display user cancellation message."""
        self._console.print("[red]Operation canceled by user.[/red]")

    def show_success(self, message: str = "") -> None:
        """Display success message.

        Args:
            message: Success message string
        """
        _text = "Operation successful." if not message else message
        self._console.print(f"[green]{_text}[/green]")

    def show_info(self, message: str) -> None:
        """Display informational message.

        Args:
            message: Informational message string
        """
        self._console.print(message)

    def show_error(self, message: str = "") -> None:
        """Display error message.

        Args:
            message: Error message string
        """
        self._console.print(f"[bold red]Error:[/bold] {message}[/red]")

    def display_networth(self, nw: NetWorth, title_suffix: str = "") -> None:
        """Display worth on a specific month.

        Args:
            nw (NetWorth): NetWorth object
            title_suffix (str): Suffix for the table title

        Returns:
            None
        """
        table = build_networth_table(nw, title_suffix, form="wide")
        self._console.print(table)
