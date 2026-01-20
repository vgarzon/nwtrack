"""
Create category interactively.
"""

import logging
from typing import Callable

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
from nwtrack.domain.models import Category, Side
from nwtrack.application.services.fetch import FetchService

logger = logging.getLogger(__name__)


class CreateCategoryInteractive:
    """Create category interactively."""

    def __init__(
        self, uow: Callable[[], UnitOfWork], fetcher: FetchService, console: Console
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._console = console
        self._prompt = Prompt(console=self._console)

    def run(self) -> None:
        logger.info("Starting Interactive Category Creator")
        self._console.rule("[bold green]Create Category[/bold green]")
        self.print_categories()
        try:
            data = self.collect_data()
        except KeyboardInterrupt as e:
            self._console.print(
                f"[red]Category creation cancelled by user:[/red] {str(e)}"
            )
            logger.warning("Category creation cancelled by user.")
            return
        if not self.validate_data(data):
            _msg = "Invalid category data provided."
            logger.error(_msg)
            self._console.print(f"[red]{_msg}[/red]")
            return

        result: str | None = self.insert_category(data)
        if result is None:
            _msg = "Category creation failed."
            logger.error(_msg)
            self._console.print(f"[red]{_msg}[/red]")
            return
        category_name: str = result
        self._console.print(
            f"[bold green]Category '{category_name}' created successfully.[/bold green]"
        )
        self.print_category_info(category_name)
        self.print_categories()
        logger.info("Finished Interactive Category Creator")

    def collect_data(self) -> Category:
        """Collect category info from user input.

        Returns:
            Category: Collected category data.
        """
        return Category(
            name=self._collect_name(),
            side=self._collect_side(),
        )

    def insert_category(self, category: Category) -> str | None:
        """Insert new category into the database.

        Args:
            category (Category): Category data to insert.

        Returns:
            str | None: The name of the created category, or None if failed.
        """
        with self._uow() as uow:
            try:
                row_count = uow.categories.insert(category)
            except ValueError as e:
                logger.exception("Error inserting category: %s", e)
                uow.rollback()
                return None

        if row_count != 1:
            logger.error("Failed to insert category: %s", category.name)
            return None

        logger.info("Inserted new category: %s", category.name)
        return category.name

    def validate_data(self, data: Category) -> bool:
        """Validate collected account data.

        Args:
            data (Category): Collected category data.

        Returns:
            bool: True if valid, False otherwise.
        """
        all_categories = self._fetcher.get_all_categories()
        for category in all_categories:
            if category.name.lower() == data.name.lower():
                logger.error("Category name '%s' already exists.", data.name)
                self._console.print(
                    f"[red]Error:[/red] Category name [bold]'{data.name}'[/bold] already exists."
                )
                return False
        # TODO: Add more validation as needed
        return True

    def _collect_name(self) -> str:
        while True:
            name = Prompt.ask("Enter [bold]category name[/bold] or 'q' to quit").strip()
            if name.lower() == "q":
                _msg = "Quit while collecting category name."
                logger.warning(_msg)
                raise KeyboardInterrupt(_msg)
            if name:
                return name
            self._console.print(
                "[magenta]Category name cannot be empty.[/magenta] Please try again."
            )

    def _collect_side(self) -> Side:
        _side = Prompt.ask(
            "Enter [bold]side[/bold] or 'q' to quit",
            choices=[side.value for side in Side] + ["q"],
            default=Side.ASSET.value,
        )
        if _side.lower() == "q":
            _msg = "Quit while collecting side."
            logger.warning(_msg)
            raise KeyboardInterrupt(_msg)
        try:
            side = Side(_side)
        except ValueError:
            self._console.print(f"[magenta]Invalid side:[/magenta] {_side}.")
            raise KeyboardInterrupt("Invalid side entered.")
        return side

    def print_categories(self) -> None:
        """Print categories."""
        categories = self._fetcher.get_all_categories()
        table = self._build_categories_table(categories)
        self._console.print(table)

    def _build_categories_table(self, categories: list[Category]) -> Table:
        """Build a Rich Table of active accounts.

        Args:
            categories (list[Category]): List of Category objects

        Returns:
            Table: Rich Table object
        """
        table = Table(title="Categories")
        table.add_column("Name", style="magenta")
        table.add_column("Side", style="yellow")
        for category in categories:
            category_name = category.name if category else "Unknown"
            side_value = category.side.value if category else "Unknown"
            table.add_row(category_name, side_value)
        return table

    def print_category_info(self, category_name: str) -> None:
        """Print category info.

        Args:
            category_name (str): Category name
        """
        result: Category | None = self._fetcher.get_category_by_name(category_name)
        if result is None:
            _msg = f"Error retrieving category '{category_name}'."
            logger.error(_msg)
            self._console.print(f"[red]{_msg}[/red]")
            return
        category: Category = result

        self._console.print(
            f"[yellow]Category name:[/yellow] {category.name}\n"
            f"[yellow]Category side:[/yellow] {category.side}"
        )


def main() -> None:
    from dotenv import load_dotenv

    from nwtrack.bootstrap.logging_config import setup_logging

    load_dotenv()
    setup_logging()

    container = build_base_sqlite_uow_container()
    container.register(
        CreateCategoryInteractive,
        lambda c: CreateCategoryInteractive(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=FetchService(uow=lambda: c.resolve(UnitOfWork)),
            console=Console(),
        ),
    )
    container.resolve(CreateCategoryInteractive).run()


if __name__ == "__main__":
    main()
