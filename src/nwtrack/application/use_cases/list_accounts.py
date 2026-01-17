"""
List accounts interactively
"""

import logging

from rich.console import Console
from rich.table import Table

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
from nwtrack.domain.models import Account

logger = logging.getLogger(__name__)


class ListAccounts:
    """List accounts interactively."""

    def __init__(self, fetcher: FetchService, console: Console) -> None:
        self._fetcher = fetcher
        self._console = console

    def run(self, active_only: bool = True) -> None:
        """Run the List Accounts use case.
        Args:
            active_only (bool): Whether to list only active accounts.
        """
        logger.info("Starting List Accounts use case")
        self.print_accounts(active_only=active_only)

        logger.info("Finished List Account")

    def print_accounts(self, active_only: bool = True) -> None:
        """Print accounts.

        Args:
            active_only (bool): Whether to print only active accounts.
        """
        accounts = self._fetcher.get_accounts(active_only=active_only)
        title_prefix = "Active" if active_only else "All"
        table = self._build_accounts_table(accounts, title_prefix=title_prefix)
        self._console.print(table)

    def _build_accounts_table(
        self, accounts: list[Account], title_prefix: str = ""
    ) -> Table:
        """Build a Rich Table of active accounts.
        Args:
            accounts (list[Account]): List of Account objects
            title_prefix (str): Optional prefix for the table title.
        Returns:
            Table: Rich Table object
        """
        _title = f"{title_prefix} Accounts" if title_prefix else "Accounts"
        table = Table(title=_title)
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Category", style="green")
        table.add_column("Side", style="yellow")
        for account in accounts:
            category = self._fetcher.get_category_by_account_id(account.id)
            category_name = category.name if category else "Unknown"
            side = category.side.value if category else "Unknown"
            table.add_row(
                str(account.id),
                account.name,
                category_name,
                side,
            )
        return table

    def print_account_data(self, account: Account) -> None:
        self._console.print(
            f"[yellow]Account ID:[/yellow] {account.id}\n"
            f"[yellow]Account name:[/yellow] {account.name}\n"
            f"[yellow]Description:[/yellow] {account.description}\n"
            f"[yellow]Currency:[/yellow] {account.currency_code}\n"
            f"[yellow]Category:[/yellow] {account.category_name}\n"
            f"[yellow]Status:[/yellow] {account.status}"
        )


def main(active_only: bool = True) -> None:
    """Main function for listing accounts interactively.
    Args:
        active_only (bool): Whether to list only active accounts.
    """
    from dotenv import load_dotenv

    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.bootstrap.container import Lifetime

    load_dotenv()
    setup_logging()

    container = build_base_sqlite_uow_container()
    container.register(
        Console,
        lambda c: Console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ListAccounts,
        lambda c: ListAccounts(
            fetcher=c.resolve(FetchService), console=c.resolve(Console)
        ),
    )
    container.resolve(ListAccounts).run(active_only=active_only)


if __name__ == "__main__":
    import sys

    argv = sys.argv[1:]
    active_only = False if "--no-active-only" in argv else True
    main(active_only=active_only)
