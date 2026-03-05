"""
Rich-based presenters for balance-related use cases.
"""

from datetime import date

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from nwtrack.domain.models import Account, Balance, NetWorth
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.prompts import (
    prompt_for_account_id,
    prompt_to_confirm_action,
)
from nwtrack.entrypoints.cli.ui.renderers import (
    build_accounts_table,
    build_balances_table,
    build_month_balances_table,
    build_networth_table,
)


class SelectableMonthMixin:
    """Mixin providing month selection functionality."""

    _console: Console
    _prompt: Prompt
    _int_prompt: IntPrompt

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

        return month

    def show_invalid_month_error(self) -> None:
        """Display error for invalid month input."""
        self._console.print("[red]Invalid month format. Please use YYYY-MM.[/red]")


class RichBalanceUpdatePresenter(SelectableMonthMixin):
    """Rich-based implementation of BalanceUpdatePresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console
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
        table = build_accounts_table(accounts, title_prefix="Active")
        self._console.print(table)

    def show_no_balances_warning(self, month: Month) -> None:
        """Display warning when no balances found for month.

        Args:
            month: The month that has no balances
        """
        self._console.print(f"[orange3]No balance entries found in {month}.[/orange3]")

    def show_no_month_selected(self) -> None:
        """Display message when no month is selected."""
        self._console.print("[orange]No month selected. Exiting.[/orange]")

    def display_balances(
        self,
        balances: list[Balance],
        month: Month,
    ) -> None:
        """Display balances table for a specific month.

        Args:
            balances: List of balances to display
            month: Month for the balances
        """
        table = build_balances_table(balances, title_suffix=str(month))
        self._console.print(table)

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

    def display_networth(self, nw: NetWorth, month: Month) -> None:
        """Display net worth table.

        Args:
            nw (NetWorth): NetWorth object
            month (Month): Month for the net worth
        """
        currency_code = "USD"  # Hardcoded for now
        title_suffix = f"{month} ({currency_code})"
        table = build_networth_table(nw, title_suffix, form="wide")
        self._console.print(table)


class RichBalancesRollForwardPresenter(SelectableMonthMixin):
    """Rich-based implementation of BalancesRollForwardPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console
        self._confirm = Confirm(console=self._console)
        self._prompt = Prompt(console=self._console)
        self._int_prompt = IntPrompt(console=self._console)

    def show_header(self) -> None:
        """Display workflow header using Rich."""
        self._console.rule("[bold green]Roll Balances Forward[/bold green]")

    def show_no_balances_warning(self, month: Month) -> None:
        """Display warning when no balances found for month.

        Args:
            month: The month that has no balances
        """
        self._console.print(f"[orange3]No balance entries found in {month}.[/orange3]")

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


class RichBalanceDeleterPresenter(SelectableMonthMixin):
    """Rich-based implementation of BalanceDeleterPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console
        self._prompt = Prompt(console=self._console)
        self._int_prompt = IntPrompt(console=self._console)
        self._confirm = Confirm(console=self._console)

    def show_header(self) -> None:
        """Display workflow header using Rich."""
        self._console.rule("[bold red]Balance Deletion[/bold red]")

    def show_no_balances_warning(self, month: Month) -> None:
        """Display warning when no balances found for month.

        Args:
            month: The month that has no balances
        """
        self._console.print(f"[orange3]No balance entries found in {month}.[/orange3]")

    def select_account(self, month: Month) -> int | None:
        """Prompt for account ID and validate it exists.

        Args:
            month (Month): Month for context

        Returns:
            int | None: Account ID or None if user quits
        """
        account_id = prompt_for_account_id(self._console)
        return account_id

    def display_balances(
        self,
        balances: list[Balance],
        title_suffix: str = "",
    ) -> None:
        table = build_balances_table(balances, title_suffix=title_suffix)
        self._console.print(table)

    def show_cancellation(self) -> None:
        """Display user cancellation message."""
        self._console.print("[red]Operation canceled by user.[/red]")

    def show_error(self, message: str = "") -> None:
        """Display error message.

        Args:
            message: Error message string
        """
        self._console.print(f"[red]Error: {message}[/red]")

    def show_balance_details(
        self, account: Account, balance: Balance, month: Month
    ) -> None:
        """Display balance details before deletion."""
        self._console.print("\n[bold]Balance to delete:[/bold]")
        self._console.print(f"  Account: {account.name} (ID: {account.id})")
        self._console.print(f"  Month: {month}")
        self._console.print(f"  Amount: {balance.amount:,}")

    def prompt_to_confirm_deletion(self) -> bool:
        """Prompt user to confirm balance deletion.

        Returns:
            True if user confirms, False otherwise
        """
        return prompt_to_confirm_action(self._console, "Delete this balance entry?")

    def show_success(self, message: str = "") -> None:
        """Display success message.

        Args:
            message: Success message string
        """
        _text = "Operation successful." if not message else message
        self._console.print(f"[green]{_text}[/green]")
