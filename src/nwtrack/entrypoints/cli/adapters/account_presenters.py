"""
Rich-based presenters for account-related use cases.
"""

from rich.console import Console

from nwtrack.application.dto import NewAccountData
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Balance, Category, Status
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.prompts import (
    prompt_for_account_description,
    prompt_for_account_name,
    prompt_for_balance_amount,
    prompt_for_category_choice,
    prompt_for_currency_choice,
    prompt_for_month,
    prompt_for_status_choice,
    prompt_to_confirm_action,
)
from nwtrack.entrypoints.cli.ui.renderers import (
    build_accounts_table,
    build_currencies_table,
    build_indexed_categories_table,
    build_status_table,
    render_new_account_info,
)


class RichAccountListPresenter:
    """Rich-based implementation of AccountListPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def display_accounts(
        self,
        accounts: list[Account],
        categories: dict[int, Category | None],
        active_only: bool = True,
    ) -> None:
        """Display accounts table using Rich.

        Args:
            accounts: List of accounts to display
            categories: Mapping of account IDs to their categories
            active_only: Whether only active accounts are shown
        """
        title_prefix = "Active" if active_only else "All"
        table = build_accounts_table(accounts, categories, title_prefix)
        self._console.print(table)


class RichAccountCreationPresenter:
    """Rich-based implementation of AccountCreationPresenter."""

    def __init__(self, console: Console, fetcher: FetchService) -> None:
        self._console = console
        self._fetcher = fetcher

    def show_header(self) -> None:
        """Display workflow header using Rich."""
        self._console.rule("[bold green]Account Creation[/bold green]")

    def display_accounts(
        self,
        accounts: list[Account],
        categories: dict[int, Category | None],
        active_only: bool = True,
    ) -> None:
        """Display existing accounts table.

        Args:
            accounts: List of accounts to display
            categories: Mapping of account IDs to their categories
            active_only: Whether only active accounts are shown
        """
        title_prefix = "Active" if active_only else "All"
        table = build_accounts_table(accounts, categories, title_prefix)
        self._console.print(table)

    def collect_account_data(self) -> NewAccountData | None:
        """Interactively collect all account data from user.

        Returns:
            NewAccountData or None if cancelled by user
        """
        try:
            return NewAccountData(
                account_name=self._collect_account_name(),
                description=self._collect_description(),
                category_name=self._collect_category_name(),
                currency_code=self._collect_currency_code(),
                status=self._collect_status(),
                initial_month=self._collect_initial_month(),
                initial_amount=self._collect_initial_balance(),
            )
        except KeyboardInterrupt:
            return None

    def _collect_account_name(self) -> str:
        """Collect account name from user."""
        while True:
            name = prompt_for_account_name(self._console)
            if name.lower() == "q":
                raise KeyboardInterrupt("Quit while collecting account name.")
            if name:
                return name
            self._console.print(
                "[magenta]Account name cannot be empty.[/magenta] Please try again."
            )

    def _collect_description(self) -> str:
        """Collect account description from user."""
        description = prompt_for_account_description(self._console)
        if description.lower() == "q":
            raise KeyboardInterrupt("Quit while collecting description.")
        return description

    def _collect_category_name(self) -> str:
        """Collect category selection from user."""
        categories = self._fetcher.get_all_categories()
        table = build_indexed_categories_table(categories)
        self._console.print(table)
        n_categories = len(categories)
        choice = prompt_for_category_choice(self._console, n_categories)
        if choice == 0:
            raise KeyboardInterrupt("Quit while collecting category name.")
        return categories[choice - 1].name

    def _collect_currency_code(self) -> str:
        """Collect currency selection from user."""
        currencies = self._fetcher.get_all_currencies()
        table = build_currencies_table(currencies)
        self._console.print(table)
        n_currencies = len(currencies)
        choice = prompt_for_currency_choice(self._console, n_currencies)
        if choice == 0:
            raise KeyboardInterrupt("Quit while collecting currency code.")
        return currencies[choice - 1].code

    def _collect_status(self) -> Status:
        """Collect status selection from user."""
        status_options = [Status.ACTIVE, Status.INACTIVE]
        table = build_status_table(status_options)
        self._console.print(table)
        choice = prompt_for_status_choice(self._console, len(status_options))
        if choice == 0:
            raise KeyboardInterrupt("Quit while collecting account status.")
        return status_options[choice - 1]

    def _collect_initial_month(self) -> Month:
        """Collect initial month from user."""
        return prompt_for_month(self._console)

    def _collect_initial_balance(self) -> int:
        """Collect initial balance amount from user."""
        return prompt_for_balance_amount(self._console)

    def show_preview_and_confirm(self, account: Account, balance: Balance) -> bool:
        """Show preview and get confirmation.

        Args:
            account: Account data to preview
            balance: Balance data to preview

        Returns:
            True if user confirms, False otherwise
        """
        self._console.print("\n[bold green]New account data:[/bold green]")
        render_new_account_info(self._console, account, balance)
        return prompt_to_confirm_action(self._console, "Create account?")

    def show_cancellation(self, message: str = "") -> None:
        """Display cancellation message.

        Args:
            message: Optional additional context
        """
        msg = "[red]Account creation cancelled.[/red]"
        if message:
            msg += f" {message}"
        self._console.print(msg)

    def show_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message to display
        """
        self._console.print(f"[red]{message}[/red]")

    def show_success(
        self,
        accounts: list[Account],
        categories: dict[int, Category | None],
    ) -> None:
        """Display success message and updated accounts list.

        Args:
            accounts: Updated list of all accounts
            categories: Mapping of account IDs to their categories
        """
        self._console.print("[bold green]Account created successfully.[/bold green]")
        self.display_accounts(accounts, categories, active_only=False)
