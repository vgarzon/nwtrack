"""
List categories
"""

import logging

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import CategoryListPresenter
from nwtrack.application.services.fetch import FetchService
from nwtrack.bootstrap.container import Container

logger = logging.getLogger(__name__)


class ListCategories:
    """List categories."""

    def __init__(
        self, fetcher: FetchService, presenter: CategoryListPresenter
    ) -> None:
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        """Run the List Categories use case.

        Returns:
            OperationResult indicating success/failure
        """
        logger.info("Starting List Categories")
        categories = self._fetcher.get_all_categories()
        self._presenter.display_categories(categories)
        logger.info("Finished List Categories")
        return OperationResult(success=True)


def bootstrap() -> Container:
    """Bootstrap the List Categories use case app.

    Returns:
        Container: Configured DI container.
    """
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.category_presenters import (
        RichCategoryListPresenter,
    )

    load_dotenv()
    setup_logging()

    container = build_base_sqlite_uow_container()
    container.register(
        Console,
        lambda _: Console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichCategoryListPresenter,
        lambda c: RichCategoryListPresenter(console=c.resolve(Console)),
    ).register(
        ListCategories,
        lambda c: ListCategories(
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(RichCategoryListPresenter),
        ),
    )
    return container


def main() -> None:
    """Main function for listing categories interactively."""
    result: OperationResult[None] = bootstrap().resolve(ListCategories).run()
    import sys

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
