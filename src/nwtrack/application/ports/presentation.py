"""
Presentation layer ports (Protocol interfaces).

These protocols define the contract between use cases (business logic)
and presentation adapters (UI implementations). Use cases depend on these
protocols, not on concrete UI implementations like Rich.
"""

from typing import Protocol

from nwtrack.application.dto import NewAccountData
from nwtrack.domain.models import Account, Balance, Category, NetWorth
from nwtrack.domain.value_objects import Month


class AccountListPresenter(Protocol):
    """Presenter for account listing workflow."""

    def display_accounts(
        self,
        accounts: list[Account],
        categories: dict[int, Category | None],
        active_only: bool = True,
    ) -> None:
        """Display accounts table.

        Args:
            accounts: List of accounts to display
            categories: Mapping of account IDs to their categories
            active_only: Whether only active accounts are shown
        """
        ...


class CategoryListPresenter(Protocol):
    """Presenter for category listing workflow."""

    def display_categories(self, categories: list[Category]) -> None:
        """Display categories table.

        Args:
            categories: List of categories to display
        """
        ...


class NetworthHistoryPresenter(Protocol):
    """Presenter for networth history report workflow."""

    def show_header(self) -> None:
        """Display report header."""
        ...

    def display_networth_history(
        self, networth_records: list[NetWorth], currency_code: str
    ) -> None:
        """Display networth history table.

        Args:
            networth_records: List of networth records to display
            currency_code: Currency code for the report
        """
        ...

    def show_no_data_warning(self, currency_code: str) -> None:
        """Display warning when no data is found.

        Args:
            currency_code: Currency code that was searched
        """
        ...

    def show_partial_data_warning(
        self, requested: int, found: int, currency_code: str
    ) -> None:
        """Display warning when fewer records than requested are found.

        Args:
            requested: Number of months requested
            found: Number of months actually found
            currency_code: Currency code for the report
        """
        ...


class CategoryCreationPresenter(Protocol):
    """Presenter for category creation workflow."""

    def show_header(self) -> None:
        """Display workflow header."""
        ...

    def display_categories(self, categories: list[Category]) -> None:
        """Display existing categories table.

        Args:
            categories: List of categories to display
        """
        ...

    def collect_category_data(self) -> Category | None:
        """Interactively collect category data from user.

        Returns:
            Category data or None if cancelled by user
        """
        ...

    def show_duplicate_error(self, category_name: str) -> None:
        """Display error when category name already exists.

        Args:
            category_name: The duplicate category name
        """
        ...

    def show_preview_and_confirm(self, category: Category) -> bool:
        """Show category preview and get confirmation.

        Args:
            category: Category data to preview

        Returns:
            True if user confirms, False otherwise
        """
        ...

    def show_cancellation(self) -> None:
        """Display cancellation message."""
        ...

    def show_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message to display
        """
        ...

    def show_success(self, category_name: str, categories: list[Category]) -> None:
        """Display success message and updated categories list.

        Args:
            category_name: Name of created category
            categories: Updated list of all categories
        """
        ...


class AccountCreationPresenter(Protocol):
    """Presenter for account creation workflow."""

    def show_header(self) -> None:
        """Display workflow header."""
        ...

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
        ...

    def collect_account_data(self) -> NewAccountData | None:
        """Interactively collect all account data from user.

        This includes: name, description, category, currency, status,
        initial month, and initial balance amount.

        Returns:
            NewAccountData or None if cancelled by user
        """
        ...

    def show_preview_and_confirm(self, account: Account, balance: Balance) -> bool:
        """Show preview of account and balance to be created, get confirmation.

        Args:
            account: Account data to preview
            balance: Balance data to preview

        Returns:
            True if user confirms, False otherwise
        """
        ...

    def show_cancellation(self, message: str = "") -> None:
        """Display cancellation message.

        Args:
            message: Optional additional context
        """
        ...

    def show_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message to display
        """
        ...

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
        ...


class AccountUpdatePresenter(Protocol):
    """Presenter for account update workflow."""

    def show_header(self) -> None:
        """Display workflow header."""
        ...

    def display_accounts(
        self,
        accounts: list[Account],
        categories: dict[int, Category | None],
        active_only: bool = False,
    ) -> None:
        """Display accounts table.

        Args:
            accounts: List of accounts to display
            categories: Mapping of account IDs to their categories
            active_only: Whether only active accounts are shown
        """
        ...

    def select_account(self) -> int | None:
        """Prompt user to select an account to update by ID.

        Returns:
            Account ID or None if cancelled
        """
        ...

    def show_account_not_found(self, account_id: int) -> None:
        """Display error when account ID is not found.

        Args:
            account_id: The account ID that was not found
        """
        ...

    def collect_updated_data(self, current_account: Account) -> Account | None:
        """Interactively collect updated account data with current values as defaults.

        Args:
            current_account: Current account data to use as defaults

        Returns:
            Updated Account or None if cancelled by user
        """
        ...

    def show_preview_and_confirm(self, updated_account: Account) -> bool:
        """Show preview of updated account and get confirmation.

        Args:
            updated_account: Updated account data to preview

        Returns:
            True if user confirms, False otherwise
        """
        ...

    def show_cancellation(self, message: str = "") -> None:
        """Display cancellation message.

        Args:
            message: Optional additional context
        """
        ...

    def show_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message to display
        """
        ...

    def show_success(self) -> None:
        """Display success message."""
        ...


class BalanceUpdatePresenter(Protocol):
    """Presenter for balance update workflow."""

    def show_header(self) -> None:
        """Display workflow header."""
        ...

    def display_active_accounts(self, accounts: list[Account]) -> None:
        """Display active accounts table.

        Args:
            accounts: List of active accounts to display
        """
        ...

    def select_month(self, balance_counts: list[tuple[Month, int]]) -> Month | None:
        """Present month selection with recent months or custom input.

        Args:
            balance_counts: List of (Month, count) tuples for recent months

        Returns:
            Selected Month or None if cancelled
        """
        ...

    def show_invalid_month_error(self) -> None:
        """Display error for invalid month input."""
        ...

    def show_no_balances_warning(self, month: Month) -> None:
        """Display warning when no balances found for month.

        Args:
            month: The month that has no balances
        """
        ...

    def show_no_month_selected(self) -> None:
        """Display message when no month is selected."""
        ...

    def display_balances(self, balances: list[Balance], month: Month) -> None:
        """Display balances table for a specific month.

        Args:
            balances: List of balances to display
            month: Month for the balances
        """
        ...

    def prompt_for_account_id(self) -> int | None:
        """Prompt for account ID to update.

        Returns:
            Account ID or None if user wants to quit the loop
        """
        ...

    def show_invalid_account_id(self) -> None:
        """Display error for invalid account ID input."""
        ...

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
        ...

    def display_final_summary(
        self, balances: list[Balance], networth: NetWorth | None, month: Month
    ) -> None:
        """Display final balances and net worth summary.

        Args:
            balances: Final list of balances
            networth: Net worth data or None if not available
            month: Month for the summary
        """
        ...


class DBInitCSVPresenter(Protocol):
    """Presenter for DB initialization from CSV workflow."""

    def show_header(self, db_file_path: str, db_ddl_path: str) -> None:
        """Display workflow header using Rich.

        Args:
            db_file_path: Path to the SQLite database file
            db_ddl_path: Path to the DDL script file
        """
        ...

    def prompt_for_file_paths(self, table_names: list[str]) -> dict[str, str]:
        """Prompt user to input CSV file paths for required tables.

        Args:
            table_names: List of required table names

        Returns:
            List of file paths as strings
        """
        ...

    def show_file_paths_table(self, file_paths: dict[str, str]) -> None:
        """Display the table of file paths.

        Args:
            file_paths: List of file paths
        """
        ...

    def prompt_for_confirmation(self) -> bool:
        """Prompt user to confirm continuation.

        Returns:
            True if user confirms, False otherwise
        """
        ...

    def show_cancellation(self) -> None:
        """Display user cancellation message."""
        ...

    def show_success(self) -> None:
        """Display successful completion message."""
        ...

    def show_error(self, message: str) -> None:
        """Display error message."""
        ...
