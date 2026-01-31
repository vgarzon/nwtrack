"""
Presentation layer ports (Protocol interfaces).

These protocols define the contract between use cases (business logic)
and presentation adapters (UI implementations). Use cases depend on these
protocols, not on concrete UI implementations like Rich.
"""

from typing import Protocol

from nwtrack.domain.models import Account, Category, NetWorth


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
