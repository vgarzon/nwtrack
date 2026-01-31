"""
Rich-based presenters for account-related use cases.
"""

from rich.console import Console

from nwtrack.domain.models import Account, Category
from nwtrack.entrypoints.cli.ui.renderers import build_accounts_table


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
