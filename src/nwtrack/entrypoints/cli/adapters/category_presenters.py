"""
Rich-based presenters for category-related use cases.
"""

from rich.console import Console

from nwtrack.domain.models import Category, Side
from nwtrack.entrypoints.cli.ui.prompts import (
    prompt_for_category_name,
    prompt_for_category_side,
    prompt_to_confirm_action,
)
from nwtrack.entrypoints.cli.ui.renderers import (
    build_categories_table,
    render_category_data,
)


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


class RichCategoryCreationPresenter:
    """Rich-based implementation of CategoryCreationPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def show_header(self) -> None:
        """Display workflow header using Rich."""
        self._console.rule("[bold green]Create Category[/bold green]")

    def display_categories(self, categories: list[Category]) -> None:
        """Display existing categories table.

        Args:
            categories: List of categories to display
        """
        table = build_categories_table(categories)
        self._console.print(table)

    def collect_category_data(self) -> Category | None:
        """Interactively collect category data from user.

        Returns:
            Category data or None if cancelled by user
        """
        try:
            name = self._collect_name()
            side = self._collect_side()
            return Category(name=name, side=side)
        except KeyboardInterrupt:
            return None

    def _collect_name(self) -> str:
        """Collect category name from user."""
        while True:
            name = prompt_for_category_name(self._console)
            if name.lower() == "q":
                raise KeyboardInterrupt("Quit while collecting category name.")
            if name:
                return name
            self._console.print(
                "[magenta]Category name cannot be empty.[/magenta] Please try again."
            )

    def _collect_side(self) -> Side:
        """Collect category side from user."""
        side_value = prompt_for_category_side(self._console)
        if side_value.lower() == "q":
            raise KeyboardInterrupt("Quit while collecting side.")
        try:
            side = Side(side_value)
        except ValueError:
            raise KeyboardInterrupt("Invalid side entered.")
        return side

    def show_duplicate_error(self, category_name: str) -> None:
        """Display error when category name already exists.

        Args:
            category_name: The duplicate category name
        """
        self._console.print(
            f"[red]Error:[/red] Category name "
            f"[bold]'{category_name}'[/bold] already exists."
        )

    def show_preview_and_confirm(self, category: Category) -> bool:
        """Show category preview and get confirmation.

        Args:
            category: Category data to preview

        Returns:
            True if user confirms, False otherwise
        """
        self._console.print("\n[bold]Category to be created:[/bold]")
        render_category_data(self._console, category)
        return prompt_to_confirm_action(self._console, "Create category?")

    def show_cancellation(self) -> None:
        """Display cancellation message."""
        self._console.print("[yellow]Category creation cancelled.[/yellow]")

    def show_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message to display
        """
        self._console.print(f"[red]{message}[/red]")

    def show_success(self, category_name: str, categories: list[Category]) -> None:
        """Display success message and updated categories list.

        Args:
            category_name: Name of created category
            categories: Updated list of all categories
        """
        self._console.print(
            f"[bold green]Category '{category_name}' created successfully.[/bold green]"
        )
        self.display_categories(categories)
