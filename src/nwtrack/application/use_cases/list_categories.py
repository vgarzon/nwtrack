"""
List categories
"""

import logging

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Category

logger = logging.getLogger(__name__)


class ListCategories:
    """List categores."""

    def __init__(self, fetcher: FetchService, console: Console) -> None:
        self._fetcher = fetcher
        self._console = console
        self._prompt = Prompt(console=self._console)

    def run(self) -> None:
        logger.info("Starting List Accounts")
        self.print_categories()
        logger.info("Finished List Accounts")

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


def main() -> None:
    from dotenv import load_dotenv

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
    from nwtrack.bootstrap.logging_config import setup_logging

    load_dotenv()
    setup_logging()

    container = build_base_sqlite_uow_container()
    container.register(
        ListCategories,
        lambda c: ListCategories(
            fetcher=FetchService(uow=lambda: c.resolve(UnitOfWork)),
            console=Console(),
        ),
    )
    container.resolve(ListCategories).run()


if __name__ == "__main__":
    main()
