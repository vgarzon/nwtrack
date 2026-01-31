"""
Create category interactively.
"""

import logging
from collections.abc import Callable

from rich.prompt import Prompt

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Category, Side
from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory
from nwtrack.entrypoints.cli.ui.prompts import (
    prompt_for_category_name,
    prompt_for_category_side,
    prompt_to_confirm_action,
)
from nwtrack.entrypoints.cli.ui.renderers import (
    build_categories_table,
    render_category_data,
)

logger = logging.getLogger(__name__)


class CreateCategoryInteractive:
    """Create category interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        console_factory: ConsoleFactory,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._console = console_factory()
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

        self._console.print("\n[bold]Category to be created:[/bold]")
        render_category_data(self._console, data)
        if not prompt_to_confirm_action(self._console, "Create category?"):
            self._console.print("[yellow]Category creation cancelled.[/yellow]")
            logger.info("Category creation cancelled by user.")
            return

        result: str | None = self.insert_category(data)
        if result is None:
            _msg = "Category creation failed."
            logger.error(_msg)
            self._console.print(f"[red]{_msg}[/red]")
            return
        category_name: str = result
        is_valid, validation_msg = self.validate_created_category(data, category_name)
        if not is_valid:
            logger.error("Created category validation failed: %s", validation_msg)
            self._console.print(f"[red]Validation failed:[/red] {validation_msg}")
            return
        self._console.print(
            f"[bold green]Category '{category_name}' created successfully.[/bold green]"
        )
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
                    f"[red]Error:[/red] Category name "
                    f"[bold]'{data.name}'[/bold] already exists."
                )
                return False
        # TODO: Add more validation as needed
        return True

    def _collect_name(self) -> str:
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
        side_value = prompt_for_category_side(self._console)
        if side_value.lower() == "q":
            raise KeyboardInterrupt("Quit while collecting side.")
        try:
            side = Side(side_value)
        except ValueError:
            logger.error("Invalid side entered: %s", side_value)
            raise KeyboardInterrupt("Invalid side entered.")
        return side

    def print_categories(self) -> None:
        """Print categories."""
        categories = self._fetcher.get_all_categories()
        table = build_categories_table(categories)
        self._console.print(table)

    def validate_created_category(
        self, data: Category, category_name: str
    ) -> tuple[bool, str]:
        """Validate that the created category matches input data.

        Args:
            data (Category): Input category data
            category_name (str): Category name

        Returns:
            tuple[bool, str]: Validation result and message
        """
        result: Category | None = self._fetcher.get_category_by_name(category_name)
        if result is None:
            _msg = f"Error retrieving category '{category_name}'."
            return False, _msg
        category: Category = result

        if category.name != data.name:
            return False, "Category name mismatch."
        if category.side != data.side:
            return False, "Category side mismatch."

        return True, "Category validated successfully."


def main() -> None:
    from dotenv import load_dotenv

    from nwtrack.bootstrap.composition import Lifetime, build_base_sqlite_uow_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings

    load_dotenv()
    setup_logging()

    console_defaults = ConsoleSettings(record=False)

    container = build_base_sqlite_uow_container()
    container.register(
        ConsoleFactory,
        lambda _: ConsoleFactory(default_settings=console_defaults),
        lifetime=Lifetime.SINGLETON,
    ).register(
        CreateCategoryInteractive,
        lambda c: CreateCategoryInteractive(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=FetchService(uow=lambda: c.resolve(UnitOfWork)),
            console_factory=c.resolve(ConsoleFactory),
        ),
    )
    container.resolve(CreateCategoryInteractive).run()


if __name__ == "__main__":
    main()
