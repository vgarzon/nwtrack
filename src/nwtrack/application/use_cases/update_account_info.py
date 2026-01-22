"""
Demo interactive use case for updating account information.
"""

import logging
from typing import Callable

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.domain.models import Account, Category, Currency, Status
from nwtrack.application.services.fetch import FetchService

logger = logging.getLogger(__name__)


class UpdateAccountInfo:
    """Update account information interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        console: Console,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._console = console

    def run(self) -> None:
        logger.info("Starting Update Account Info use case")
        self._console.rule("[bold green]Update Account Info[/bold green]")
        try:
            account_id = self.select_account_to_update()
        except KeyboardInterrupt as e:
            _msg = "Account update cancelled by user."
            self._console.print(f"[magenta]{_msg}/magenta]", str(e))
            logger.warning(_msg)
            return
        try:
            updated_account = self.collect_data(account_id)
        except KeyboardInterrupt as e:
            _msg = "Account update cancelled by user."
            self._console.print(f"[magenta]{_msg}[/magenta]", str(e))
            logger.warning(_msg)
            return

        self._console.print("[bold]Updated account data[/bold]")
        self.print_account_data(updated_account)
        proceed = Confirm.ask("Proceed with update", default=False)
        if not proceed:
            self._console.print("[magenta]Stopping.[/magenta]")
            logger.warning("Stopping without updating database.")
            return

        self.update_repo(updated_account)
        success = self.confirm_update(account_id, updated_account)
        if not success:
            _msg = "Account update verification failed."
            self._console.print(f"[red]{_msg}[/red]")
            logger.error(_msg)
            return

        self._console.print("\n[bold green]Account updated successfully.[/bold green]")
        logger.info("Finished Account Updater")

    def update_repo(self, updated_account: Account) -> None:
        """Update account data in the database.
        Args:
            updated_account (Account): New account data.
        """
        with self._uow() as uow:
            uow.accounts.update(updated_account)

    def select_account_to_update(self) -> int:
        self.print_accounts(active_only=False)
        while True:
            account_id = IntPrompt.ask(
                "Enter [bold]account ID[/bold] to update or '0' to quit",
                default=0,
            )
            if account_id == 0:
                logger.warning("Quit while selecting account to update.")
                raise KeyboardInterrupt("Quit while selecting account to update.")
            account = self._fetcher.get_account_by_id(account_id)
            if account:
                return account_id
            else:
                self._console.print(
                    f"[magenta]Account ID {account_id} not found.[/magenta] Please try again."
                )

    def collect_data(self, account_id: int) -> Account:
        """Collect new account info from user input.

        Args:
            account_id (int): ID of the account to update.
        Returns:
            Account: Collected account data.
        """
        account = self._fetcher.get_account_by_id(account_id)
        if account is None:
            raise ValueError(f"Account ID {account_id} not found.")

        self._console.print(
            f"Updating account [bold]{account.name}[/bold] (ID: {account.id})"
        )
        new_account_name = self._collect_account_name(default=account.name)
        new_description = self._collect_description(default=account.description)
        new_category_name = self._collect_category_name(default=account.category_name)
        new_currency_code = self._collect_currency_code(default=account.currency_code)
        new_status = self._collect_status(default=account.status)

        return Account(
            id=account_id,
            name=new_account_name,
            description=new_description,
            category_name=new_category_name,
            currency_code=new_currency_code,
            status=new_status,
        )

    def print_accounts(self, active_only: bool = True) -> None:
        """Print accounts.

        Args:
            active_only (bool): Whether to print only active accounts.
        """
        if active_only:
            accounts = self._fetcher.get_accounts(active_only=True)
            title_prefix = "Active"
        else:
            accounts = self._fetcher.get_accounts(active_only=False)
            title_prefix = "All"
        table = self._build_accounts_table(accounts, title_prefix=title_prefix)
        self._console.print(table)

    def print_account_data(self, account: Account) -> None:
        self._console.print(
            f"[yellow]Account ID:[/yellow] {account.id}\n"
            f"[yellow]Account name:[/yellow] {account.name}\n"
            f"[yellow]Description:[/yellow] {account.description}\n"
            f"[yellow]Currency:[/yellow] {account.currency_code}\n"
            f"[yellow]Category:[/yellow] {account.category_name}\n"
            f"[yellow]Status:[/yellow] {account.status}"
        )

    def confirm_update(self, account_id: int, update_data: Account) -> bool:
        """Confirm that the account was updated correctly.
        Args:
            account_id (int): Account ID
            update_data (Account): Updated account data
        Returns:
            bool: True if update was successful, False otherwise.
        """
        retrieved_data: Account | None = self._fetcher.get_account_by_id(account_id)
        if retrieved_data is None:
            _msg = "Error retrieving newly created account or balance."
            logger.error(_msg)
            self._console.print(f"[red]{_msg}[/red]")
            return False
        return retrieved_data == update_data

    def _collect_account_name(self, default="") -> str:
        """Input account name from user.
        Args:
            default (str): Default account name.
        Returns:
            str: Account name.
        """
        while True:
            name = Prompt.ask(
                "Enter [bold]account name[/bold] or 'q' to quit",
                default=default,
            ).strip()
            if name.lower() == "q":
                logger.warning("Quit while collecting account name.")
                raise KeyboardInterrupt("Quit while collecting account name.")
            # TODO: Add string validation rules here
            if name:
                return name
            self._console.print(
                "[magenta]Account name cannot be empty.[/magenta] Please try again."
            )

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

    def _collect_description(self, default="") -> str:
        """Input account description from user.
        Args:
            default (str): Default description.
        Returns:
            str: Description.
        """
        description = Prompt.ask(
            "Enter optional [bold]description[/bold] or 'q' to quit",
            default=default,
        ).strip()
        if description.lower() == "q":
            logger.warning("Quit while collecting description.")
            raise KeyboardInterrupt("Quit while collecting description.")
        return description

    def _collect_category_name(self, default="") -> str:
        """Input category name from user.
        Args:
            default (str): Default category name.
        Returns:
            str: Category name.
        """
        categories = self._fetcher.get_all_categories()
        if default != "":
            default_index = next(
                (i + 1 for i, cat in enumerate(categories) if cat.name == default), 0
            )
        else:
            default_index = 0
        table = self._build_categories_table(categories)
        self._console.print(table)
        while True:
            choice = IntPrompt.ask(
                "Enter [bold]category index[/bold] or '0' to quit",
                default=default_index,
                choices=[str(i) for i in range(len(categories) + 1)],
            )
            if choice == 0:
                logger.warning("Quit while collecting category name.")
                raise KeyboardInterrupt("Quit while collecting category name.")
            index = choice - 1
            if 0 <= index < len(categories):
                break
            else:
                self._console.print(
                    "[magenta]Invalid choice.[/magenta] Please try again."
                )
        return categories[index].name

    def _build_categories_table(self, categories: list[Category]) -> Table:
        table = Table(title="Categories")
        table.add_column("Index", justify="right", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Side", style="green")
        for k, category in enumerate(categories):
            table.add_row(
                str(k + 1),
                category.name,
                category.side.value,
            )
        return table

    def _collect_currency_code(self, default="") -> str:
        """Input currency code from user.
        Args:
            default (str): Default currency code.
        Returns:
            str: Currency code.
        """
        currencies = self._fetcher.get_all_currencies()
        if default != "":
            default_index = next(
                (i + 1 for i, cur in enumerate(currencies) if cur.code == default), 1
            )
        else:
            default_index = 1
        table = self._build_currencies_table(currencies)
        self._console.print(table)
        while True:
            choice = IntPrompt.ask(
                "Enter [bold]currency index[/bold] or '0' to quit",
                default=default_index,
                choices=[str(i) for i in range(len(currencies) + 1)],
            )
            if choice == 0:
                logger.warning("Quit while collecting currency code.")
                raise KeyboardInterrupt("Quit while collecting currency code.")
            index = choice - 1
            if 0 <= index < len(currencies):
                break
            else:
                self._console.print(
                    "[magenta]Invalid choice.[/magenta] Please try again."
                )
        return currencies[index].code

    def _build_currencies_table(self, currencies: list[Currency]) -> Table:
        table = Table(title="Currencies")
        table.add_column("Index", justify="right", style="cyan", no_wrap=True)
        table.add_column("Code", style="magenta")
        table.add_column("Description", style="green")
        for k, currency in enumerate(currencies):
            table.add_row(
                str(k + 1),
                currency.code,
                currency.description,
            )
        return table

    def _collect_status(self, default=Status.ACTIVE) -> Status:
        status_options = [Status.ACTIVE, Status.INACTIVE]
        default_index = status_options.index(default) + 1
        table = self._build_status_table(status_options)
        self._console.print(table)
        choice = IntPrompt.ask(
            "Select [bold]account status[/bold] by index or '0' to quit",
            default=default_index,
            choices=["0", "1", "2"],
        )
        if choice == 0:
            logger.warning("Quit while collecting account status.")
            raise KeyboardInterrupt("Quit while collecting account status.")
        index = choice - 1
        return status_options[index]

    def _build_status_table(self, status_options: list[Status]) -> Table:
        table = Table(title="Status Options")
        table.add_column("Index", justify="right", style="cyan", no_wrap=True)
        table.add_column("Status", style="magenta")
        for k, status in enumerate(status_options):
            table.add_row(
                str(k + 1),
                status.value,
            )
        return table


def main() -> None:
    from dotenv import load_dotenv

    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.bootstrap.composition import build_base_sqlite_uow_container, Lifetime

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
        UpdateAccountInfo,
        lambda c: UpdateAccountInfo(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            console=c.resolve(Console),
        ),
    )
    container.resolve(UpdateAccountInfo).run()


if __name__ == "__main__":
    main()
