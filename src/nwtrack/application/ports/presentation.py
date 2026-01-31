"""
Presentation layer ports (Protocol interfaces).

These protocols define the contract between use cases (business logic)
and presentation adapters (UI implementations). Use cases depend on these
protocols, not on concrete UI implementations like Rich.
"""

from typing import Protocol

from nwtrack.domain.models import Account, Category


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
