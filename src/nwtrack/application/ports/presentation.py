"""
Presentation layer ports (Protocol interfaces).

These protocols define the contract between use cases (business logic)
and presentation adapters (UI implementations). Use cases depend on these
protocols, not on concrete UI implementations like Rich.
"""

from typing import Protocol

from nwtrack.application.dto import (
    InstitutionListItem,
    MonthlyCategoryBalance,
    NewAccountData,
    TagListItem,
    UpdatedAccountData,
)
from nwtrack.domain.models import Account, Balance, Category, Institution, NetWorth, Tag
from nwtrack.domain.value_objects import Month


class AccountListPresenter(Protocol):
    """Presenter for account listing workflow."""

    def display_accounts(
        self,
        accounts: list[Account],
        active_only: bool = True,
    ) -> None:
        """Display accounts table.

        Args:
            accounts: List of accounts to display
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


class InstitutionListPresenter(Protocol):
    """Presenter for institution listing workflow."""

    def display_institutions(self, institutions: list[InstitutionListItem]) -> None:
        """Display institutions table."""
        ...


class TagListPresenter(Protocol):
    """Presenter for tag listing workflow."""

    def display_tags(self, tags: list[TagListItem]) -> None:
        """Display tags table."""
        ...


class TagCreationPresenter(Protocol):
    """Presenter for tag creation workflow."""

    def show_header(self) -> None: ...

    def display_tags(self, tags: list[TagListItem]) -> None: ...

    def collect_tag_data(self) -> Tag | None: ...

    def show_duplicate_error(self, tag_name: str) -> None: ...

    def show_empty_name_error(self) -> None: ...

    def show_preview_and_confirm(self, tag: Tag) -> bool: ...

    def show_cancellation(self) -> None: ...

    def show_error(self, message: str) -> None: ...

    def show_success(self, tag_name: str, tags: list[TagListItem]) -> None: ...


class TagUpdatePresenter(Protocol):
    """Presenter for tag update workflow."""

    def show_header(self) -> None: ...

    def display_tags(self, tags: list[TagListItem]) -> None: ...

    def show_no_tags(self) -> None: ...

    def select_tag(self) -> int | None: ...

    def show_tag_not_found(self, tag_id: int) -> None: ...

    def collect_updated_data(self, current_tag: Tag) -> Tag | None: ...

    def show_duplicate_error(self, tag_name: str) -> None: ...

    def show_empty_name_error(self) -> None: ...

    def show_preview_and_confirm(self, tag: Tag) -> bool: ...

    def show_cancellation(self, message: str = "") -> None: ...

    def show_error(self, message: str) -> None: ...

    def show_success(self, tags: list[TagListItem]) -> None: ...


class TagDeletePresenter(Protocol):
    """Presenter for tag deletion workflow."""

    def show_header(self) -> None: ...

    def display_tags(self, tags: list[TagListItem]) -> None: ...

    def show_no_tags(self) -> None: ...

    def select_tag(self) -> int | None: ...

    def show_tag_not_found(self, tag_id: int) -> None: ...

    def show_preview_and_confirm(self, tag: Tag, account_count: int) -> bool: ...

    def show_delete_blocked(self, tag: Tag, account_count: int) -> None: ...

    def show_cancellation(self, message: str = "") -> None: ...

    def show_error(self, message: str) -> None: ...

    def show_success(self, tags: list[TagListItem]) -> None: ...


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

    def display_total_change(
        self, networth_records: list[NetWorth], currency_code: str
    ) -> None:
        """Display total change in net worth over the period."""
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


class InstitutionCreationPresenter(Protocol):
    """Presenter for institution creation workflow."""

    def show_header(self) -> None: ...

    def display_institutions(self, institutions: list[InstitutionListItem]) -> None: ...

    def collect_institution_data(self) -> Institution | None: ...

    def show_duplicate_error(self, institution_name: str) -> None: ...

    def show_preview_and_confirm(self, institution: Institution) -> bool: ...

    def show_cancellation(self) -> None: ...

    def show_error(self, message: str) -> None: ...

    def show_success(
        self,
        institution_name: str,
        institutions: list[InstitutionListItem],
    ) -> None: ...


class AccountCreationPresenter(Protocol):
    """Presenter for account creation workflow."""

    def show_header(self) -> None:
        """Display workflow header."""
        ...

    def display_accounts(
        self,
        accounts: list[Account],
        active_only: bool = True,
    ) -> None:
        """Display existing accounts table.

        Args:
            accounts: List of accounts to display
            active_only: Whether only active accounts are shown
        """
        ...

    def collect_account_data(self) -> NewAccountData | None:
        """Interactively collect all account data from user.

        This includes: institution, tags, name, description, category, currency,
        status, initial month, and initial balance amount.

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
    ) -> None:
        """Display success message and updated accounts list.

        Args:
            accounts: Updated list of all accounts
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
        active_only: bool = False,
    ) -> None:
        """Display accounts table.

        Args:
            accounts: List of accounts to display
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

    def collect_updated_data(
        self, current_account: Account
    ) -> UpdatedAccountData | None:
        """Interactively collect updated account data with current values as defaults.

        Args:
            current_account: Current account data to use as defaults

        Returns:
            Updated account input data with preserved or updated institution and tag
            assignment, or None if cancelled by user
        """
        ...

    def show_preview_and_confirm(self, updated_account: UpdatedAccountData) -> bool:
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


class InstitutionUpdatePresenter(Protocol):
    """Presenter for institution update workflow."""

    def show_header(self) -> None: ...

    def display_institutions(self, institutions: list[InstitutionListItem]) -> None: ...

    def show_no_institutions(self) -> None: ...

    def select_institution(self) -> int | None: ...

    def show_institution_not_found(self, institution_id: int) -> None: ...

    def collect_updated_data(
        self, current_institution: Institution
    ) -> Institution | None: ...

    def show_duplicate_error(self, institution_name: str) -> None: ...

    def show_preview_and_confirm(self, institution: Institution) -> bool: ...

    def show_cancellation(self, message: str = "") -> None: ...

    def show_error(self, message: str) -> None: ...

    def show_success(self, institutions: list[InstitutionListItem]) -> None: ...


class InstitutionDeletePresenter(Protocol):
    """Presenter for institution delete workflow."""

    def show_header(self) -> None: ...

    def display_institutions(self, institutions: list[InstitutionListItem]) -> None: ...

    def show_no_institutions(self) -> None: ...

    def select_institution(self) -> int | None: ...

    def show_institution_not_found(self, institution_id: int) -> None: ...

    def show_preview_and_confirm(
        self, institution: Institution, account_count: int
    ) -> bool: ...

    def show_delete_blocked(self, institution: Institution, account_count: int) -> None:
        ...

    def show_cancellation(self, message: str = "") -> None: ...

    def show_error(self, message: str) -> None: ...

    def show_success(self, institutions: list[InstitutionListItem]) -> None: ...


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

    def display_networth(self, nw: NetWorth, month: Month) -> None:
        """Display net worth table.

        Args:
            nw (NetWorth): NetWorth object
            month (Month): Month for the net worth
        """
        ...


class BalanceCreationPresenter(Protocol):
    """Presenter for balance creation workflow."""

    def show_header(self) -> None:
        """Display workflow header."""
        ...

    def display_active_accounts(self, accounts: list[Account]) -> None:
        """Display active accounts eligible for balance creation."""
        ...

    def select_account(self) -> int | None:
        """Prompt for an account ID or cancellation."""
        ...

    def show_no_active_accounts(self) -> None:
        """Display empty-state message when no active accounts are available."""
        ...

    def show_account_not_found(self, account_id: int) -> None:
        """Display validation when the selected account is not eligible."""
        ...

    def collect_month(self) -> Month | None:
        """Collect the month for the new balance."""
        ...

    def collect_amount(self) -> int | None:
        """Collect the amount for the new balance."""
        ...

    def show_preview_and_confirm(self, account: Account, balance: Balance) -> bool:
        """Preview the new balance entry and confirm creation."""
        ...

    def show_duplicate_error(self, account: Account, month: Month) -> None:
        """Display duplicate-balance validation with update guidance."""
        ...

    def show_cancellation(self, message: str = "") -> None:
        """Display cancellation message."""
        ...

    def show_error(self, message: str) -> None:
        """Display error message."""
        ...

    def show_success(self, account: Account, balance: Balance) -> None:
        """Display success message and created-balance preview."""
        ...


class DBInitCSVPresenter(Protocol):
    """Presenter for DB initialization from CSV workflow."""

    def show_header(self, db_file_path: str) -> None:
        """Display workflow header.

        Args:
            db_file_path: Path to the SQLite database file
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


class BalancesByCategoryPresenter(Protocol):
    """Presenter for balances by category report workflow."""

    def show_header(self) -> None:
        """Display report header."""
        ...

    def show_accounts_table(
        self,
        accounts: list[Account],
        title_prefix: str = "",
    ) -> None: ...

    def show_balances_table(
        self,
        balances: list[Balance],
        title_suffix: str = "",
    ) -> None:
        """Show balances table with account and category information.

        Args:
            balances: List of balances
            title_suffix: Suffix for the table title

        Returns:
            None
        """
        ...

    def show_summary_by_category(
        self, monthly_balances: list[MonthlyCategoryBalance], title_suffix: str = ""
    ) -> None:
        """Print summary by category for a specific month.

        Args:
            monthly_balances: list[MonthlyCategoryBalance]
            title_suffix: Suffix for the table title
        """
        ...

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
        ...

    def prompt_for_month_choice(
        self, balance_counts: list[tuple[Month, int]]
    ) -> Month | None:
        """Present month selection with recent months or custom input.

        Args:
            balance_counts: List of (Month, count) tuples for recent months

        Returns:
            Selected Month or None if cancelled
        """
        ...

    def _input_custom_month(self) -> Month | None:
        """Input a specific month from user."""
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

    def show_no_month_selected_message(self) -> None:
        """Display messag3 when no month is selected."""
        ...

    def show_no_networth_data_warning(self, month: Month, currency_code: str) -> None:
        """Display warning when no net worth data found for month and currency.

        Args:
            month: The month that has no net worth data
            currency_code: The currency code that was searched
        """
        ...


class BalancesRollForwardPresenter(Protocol):
    """Presenter for balances roll forward workflow."""

    def show_header(self) -> None:
        """Display workflow header."""
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

    def confirm_target_month(self, target_month: Month) -> bool:
        """Prompt user to confirm rolling balances forward.

        Args:
            target_month: The month to roll balances into

        Returns:
            True if user confirms, False otherwise
        """
        ...

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
        ...

    def show_cancellation(self) -> None:
        """Display user cancellation message."""
        ...

    def show_success(self, message: str = "") -> None:
        """Display success message.

        Args:
            message: Success message string
        """
        ...

    def show_info(self, message: str) -> None:
        """Display informational message.

        Args:
            message: Informational message string
        """
        ...

    def show_error(self, message: str = "") -> None:
        """Display error message.

        Args:
            message: Error message string
        """
        ...

    def display_networth(self, nw: NetWorth, title_suffix: str = "") -> None:
        """Display worth on a specific month.

        Args:
            nw (NetWorth): NetWorth object
            title_suffix (str): Suffix for the table title

        Returns:
            None
        """
        ...

    def show_no_balances_warning(self, month: Month) -> None:
        """Display warning when no balances found for month.

        Args:
            month: The month that has no balances
        """
        ...


class BalanceDeleterPresenter(Protocol):
    """Presenter for BalanceDeleter workflow."""

    def show_header(self) -> None:
        """Display workflow header."""
        ...

    def select_month(self, balance_counts: list[tuple[Month, int]]) -> Month | None:
        """Present month selection with recent months or custom input.

        Args:
            balance_counts: List of (Month, count) tuples for recent months

        Returns:
            Selected Month or None if cancelled
        """
        ...

    def _input_custom_month(self) -> Month | None:
        """Input a specific month from user."""
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

    def select_account(self, month: Month) -> int | None:
        """Prompt for account ID and validate it exists.

        Args:
            month (Month): Month for context

        Returns:
            int | None: Account ID or None if user quits
        """
        ...

    def display_balances(
        self,
        balances: list[Balance],
        title_suffix: str = "",
    ) -> None:
        """Show balances table with account and category information.

        Args:
            balances: List of balances
            title_suffix: Suffix for the table title
        """
        ...

    def show_cancellation(self) -> None:
        """Display user cancellation message."""
        ...

    def show_error(self, message: str = "") -> None:
        """Display error message.

        Args:
            message: Error message string
        """
        ...

    def show_balance_details(
        self, account: Account, balance: Balance, month: Month
    ) -> None:
        """Display balance details before deletion."""
        ...

    def prompt_to_confirm_deletion(self) -> bool:
        """Prompt user to confirm balance deletion.

        Returns:
            True if user confirms, False otherwise
        """
        ...

    def show_success(self, message: str = "") -> None:
        """Display success message.

        Args:
            message: Success message string
        """
        ...


class BalanceTransferPresenter(Protocol):
    """Presenter for BalanceTransfer workflow."""

    def show_header(self) -> None:
        """Display workflow header."""
        ...

    def select_month(self, balance_counts: list[tuple[Month, int]]) -> Month | None:
        """Present month selection with recent months or custom input.

        Args:
            balance_counts: List of (Month, count) tuples for recent months

        Returns:
            Selected Month or None if cancelled
        """
        ...

    def _input_custom_month(self) -> Month | None:
        """Input a specific month from user."""
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

    def display_balances(
        self,
        balances: list[Balance],
        title_suffix: str = "",
    ) -> None:
        """Show balances table.

        Args:
            balances: List of balances
            title_suffix: Suffix for the table title
        """
        ...

    def select_from_account(self, month: Month) -> int | None:
        """Prompt for source account ID.

        Args:
            month: Month for context

        Returns:
            Account ID or None if user cancelled
        """
        ...

    def select_to_account(self, month: Month) -> int | None:
        """Prompt for destination account ID.

        Args:
            month: Month for context

        Returns:
            Account ID or None if user cancelled
        """
        ...

    def prompt_for_transfer_amount(self) -> int:
        """Prompt for the transfer amount (positive integer).

        Returns:
            Transfer amount as a positive integer
        """
        ...

    def show_transfer_preview(
        self,
        from_account: Account,
        to_account: Account,
        month: Month,
        amount: int,
        from_delta: int,
        to_delta: int,
    ) -> None:
        """Display a preview of the transfer effect on both balances.

        Args:
            from_account: Source account
            to_account: Destination account
            month: Month for the transfer
            amount: Transfer amount
            from_delta: Change applied to from_account balance
            to_delta: Change applied to to_account balance
        """
        ...

    def prompt_to_confirm_transfer(self) -> bool:
        """Prompt user to confirm the transfer.

        Returns:
            True if confirmed, False otherwise
        """
        ...

    def show_cancellation(self) -> None:
        """Display user cancellation message."""
        ...

    def show_error(self, message: str = "") -> None:
        """Display error message.

        Args:
            message: Error message string
        """
        ...

    def show_success(self, message: str = "") -> None:
        """Display success message.

        Args:
            message: Success message string
        """
        ...
