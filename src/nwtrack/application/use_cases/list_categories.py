"""
List categories
"""

import logging

from nwtrack.application.services.fetch import FetchService
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory
from nwtrack.entrypoints.cli.ui.renderers import build_categories_table

logger = logging.getLogger(__name__)


class ListCategories:
    """List categores."""

    def __init__(self, fetcher: FetchService, console_factory: ConsoleFactory) -> None:
        self._fetcher = fetcher
        self._console = console_factory()

    def run(self) -> None:
        logger.info("Starting List Accounts")
        categories = self._fetcher.get_all_categories()
        table = build_categories_table(categories)
        self._console.print(table)
        logger.info("Finished List Accounts")


def bootstrap() -> Container:
    """Bootstrap the List Categories use case app.

    Returns:
        Container: Configured DI container.
    """
    from dotenv import load_dotenv

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings

    load_dotenv()
    setup_logging()

    console_settings = ConsoleSettings(record=False)

    container = build_base_sqlite_uow_container()
    container.register(
        ConsoleFactory,
        lambda _: ConsoleFactory(default_settings=console_settings),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ListCategories,
        lambda c: ListCategories(
            fetcher=c.resolve(FetchService),
            console_factory=c.resolve(ConsoleFactory),
        ),
    )
    return container


def main() -> None:
    """Main function for listing categories interactively."""
    bootstrap().resolve(ListCategories).run()


if __name__ == "__main__":
    main()
