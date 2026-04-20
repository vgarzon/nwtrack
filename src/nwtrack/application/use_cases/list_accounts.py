"""
List accounts interactively
"""

import logging

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import AccountListPresenter
from nwtrack.application.services.fetch import FetchService
from nwtrack.bootstrap.composition import build_base_container

logger = logging.getLogger(__name__)


class ListAccounts:
    """List accounts interactively."""

    def __init__(self, fetcher: FetchService, presenter: AccountListPresenter) -> None:
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self, active_only: bool = True) -> OperationResult[None]:
        """Run the List Accounts use case.

        Args:
            active_only: Whether to list only active accounts.

        Returns:
            OperationResult indicating success/failure
        """
        logger.info("Starting List Accounts use case")
        accounts = self._fetcher.get_accounts(active_only=active_only)
        self._presenter.display_accounts(accounts, active_only)
        logger.info("Finished List Account")
        return OperationResult(success=True)


def main(active_only: bool = True) -> int:
    """Main function for listing accounts interactively.

    Args:
        active_only: Whether to list only active accounts.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.account_presenters import (
        RichAccountListPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    load_dotenv()
    setup_logging()

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichAccountListPresenter,
        lambda c: RichAccountListPresenter(console=c.resolve(Console)),
    ).register(
        ListAccounts,
        lambda c: ListAccounts(
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(RichAccountListPresenter),
        ),
    )

    result: OperationResult[None] = container.resolve(ListAccounts).run(
        active_only=active_only
    )
    return 0 if result.success else 1


if __name__ == "__main__":
    import sys

    argv = sys.argv[1:]
    active_only = False if "--no-active-only" in argv else True
    sys.exit(main(active_only=active_only))
