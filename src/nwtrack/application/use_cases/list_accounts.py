"""
List accounts interactively
"""

import logging

from nwtrack.application.services.fetch import FetchService
from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
from nwtrack.domain.models import Account, Category
from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory
from nwtrack.entrypoints.cli.ui.renderers import build_accounts_table

logger = logging.getLogger(__name__)


class ListAccounts:
    """List accounts interactively."""

    def __init__(self, fetcher: FetchService, console_factory: ConsoleFactory) -> None:
        self._fetcher = fetcher
        self._console = console_factory()

    def run(self, active_only: bool = True) -> None:
        """Run the List Accounts use case.
        Args:
            active_only (bool): Whether to list only active accounts.
        """
        logger.info("Starting List Accounts use case")
        accounts, category_map = self._fetch_account_data(active_only=active_only)
        title_prefix = "Active" if active_only else "All"
        table = build_accounts_table(accounts, category_map, title_prefix)
        self._console.print(table)
        logger.info("Finished List Account")

    def _fetch_account_data(
        self, active_only: bool = True
    ) -> tuple[list[Account], dict[int, Category]]:
        """Build the accounts table.

        Args:
            active_only (bool): Whether to print only active accounts.

        Returns:
            tuple[list[Account], dict[int, Category]]: List of accounts and
                mapping of account IDs to categories.
        """
        accounts = self._fetcher.get_accounts(active_only=active_only)
        categories_map = {
            account.id: self._fetcher.get_category_by_account_id(account.id)
            for account in accounts
        }
        return accounts, categories_map


def main(active_only: bool = True) -> None:
    """Main function for listing accounts interactively.
    Args:
        active_only (bool): Whether to list only active accounts.
    """
    from dotenv import load_dotenv

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings

    load_dotenv()
    setup_logging()

    console_default = ConsoleSettings(width=None, record=False)

    container = build_base_sqlite_uow_container()
    container.register(
        ConsoleFactory,
        lambda _: ConsoleFactory(default_settings=console_default),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ListAccounts,
        lambda c: ListAccounts(
            fetcher=c.resolve(FetchService), console_factory=c.resolve(ConsoleFactory)
        ),
    )
    container.resolve(ListAccounts).run(active_only=active_only)


if __name__ == "__main__":
    import sys

    argv = sys.argv[1:]
    active_only = False if "--no-active-only" in argv else True
    main(active_only=active_only)
