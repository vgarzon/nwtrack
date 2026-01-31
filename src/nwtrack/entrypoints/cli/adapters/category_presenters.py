"""
Rich-based presenters for category-related use cases.
"""

from rich.console import Console

from nwtrack.domain.models import Category
from nwtrack.entrypoints.cli.ui.renderers import build_categories_table


class RichCategoryListPresenter:
    """Rich-based implementation of CategoryListPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def display_categories(self, categories: list[Category]) -> None:
        """Display categories table using Rich.

        Args:
            categories: List of categories to display
        """
        table = build_categories_table(categories)
        self._console.print(table)
