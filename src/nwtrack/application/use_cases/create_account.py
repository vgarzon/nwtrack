"""
Demo interactive account creation use case.
"""

import logging
from typing import Callable

from rich.console import Console
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.dto import NewAccountData
from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
from nwtrack.domain.models import Account, Balance, Category, Currency, Status
from nwtrack.domain.value_objects import Month
from nwtrack.application.services.fetch import FetchService

logger = logging.getLogger(__name__)


class AccountCreator:
    """Create account interactively."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow
        # TODO: Inject FetchService and Coonsole via container -- see ListAccounts
        self._fetcher = FetchService(uow)
        self._console = Console()

    def run(self) -> None:
        logger.info("Starting Account Creator")
        self._console.rule("[bold green]Account Creation[/bold green]")
        self.print_accounts(active_only=True)
        try:
            data = self.collect_data()
        except KeyboardInterrupt as e:
            print("Account creation cancelled by user:", str(e))
            logger.warning("Account creation cancelled by user.")
            return

        res: tuple | None = self.create_account_and_balance(data)
        if res is None:
            _msg = "Account creation failed."
            logger.error(_msg)
            self._console.print(f"[red]{_msg}[/red]")
            return
        account_id, balance_id = res

        check = self.validate_new_account(data, account_id, balance_id)
        if not check:
            raise ValueError("New account validation failed.")
            return

        self.print_new_account_info(account_id, balance_id)
        self.print_accounts(active_only=False)
        logger.info("Finished Account Creator")

    def create_account_and_balance(
        self, data: NewAccountData
    ) -> tuple[int, int] | None:
        """Create account and initial balance in the database.

        Args:
            data (NewAccountData): Collected account data.

        Returns:
            tuple[int, int] | None: Tuple of account ID and balance ID, or None
        """
        with self._uow() as uow:
            account = Account(
                id=0,
                name=data.account_name,
                description=data.description,
                category_name=data.category_name,
                currency_code=data.currency_code,
                status=data.status,
            )
            try:
                account_id = uow.accounts.insert(account)
            except ValueError as e:
                logger.exception("Error inserting account: %s", e)
                uow.rollback()
                return None
            balance = Balance(
                id=0,
                account_id=account_id,
                month=data.initial_month,
                amount=data.initial_amount,
            )
            try:
                balance_id = uow.balances.insert(balance)
            except ValueError as e:
                logger.exception("Error inserting balance: %s", e)
                uow.rollback()
                return None
        return account_id, balance_id

    def collect_data(self) -> NewAccountData:
        """Collect account info from user input.

        Returns:
            NewAccountData: Collected account data.
        """
        return NewAccountData(
            account_name=self._collect_account_name(),
            description=self._collect_description(),
            category_name=self._collect_category_name(),
            currency_code=self._collect_currency_code(),
            status=self._collect_status(),
            initial_month=self._collect_initial_month(),
            initial_amount=self._collect_initial_balance(),
        )

    def _collect_account_name(self) -> str:
        while True:
            name = Prompt.ask("Enter [bold]account name[/bold] or 'q' to quit").strip()
            if name.lower() == "q":
                logger.warning("Quit while collecting account name.")
                raise KeyboardInterrupt("Quit while collecting account name.")
            # TODO: Add string validation rules here
            if name:
                return name
            self._console.print(
                "[magenta]Account name cannot be empty.[/magenta] Please try again."
            )

    def _collect_description(self) -> str:
        description = Prompt.ask(
            "Enter optional [bold]description[/bold] or 'q' to quit: "
        ).strip()
        if description.lower() == "q":
            logger.warning("Quit while collecting description.")
            raise KeyboardInterrupt("Quit while collecting description.")
        return description

    def _collect_category_name(self) -> str:
        categories = self._fetcher.get_all_categories()
        table = self._build_categories_table(categories)
        self._console.print(table)
        while True:
            choice = IntPrompt.ask(
                "Enter [bold]category index[/bold] or '0' to quit",
                default=0,
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

    def _collect_currency_code(self) -> str:
        currencies = self._fetcher.get_all_currencies()
        table = self._build_currencies_table(currencies)
        self._console.print(table)
        while True:
            choice = IntPrompt.ask(
                "Enter [bold]currency index[/bold] or '0' to quit",
                default=1,
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

    def _collect_status(self) -> Status:
        status_options = [Status.ACTIVE, Status.INACTIVE]
        table = self._build_status_table(status_options)
        self._console.print(table)
        choice = IntPrompt.ask(
            "Select [bold]account status[/bold] by index or '0' to quit",
            default=1,
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

    def _collect_initial_month(self) -> Month:
        """Input initial month from user.

        Returns:
            Month: Month object
        """
        from datetime import date

        _today = date.today()
        while True:
            _year = IntPrompt.ask(
                "Enter initial [bold]year[/bold] as 'YYYY'", default=_today.year
            )
            _month = IntPrompt.ask(
                "Enter initial [bold]month[/bold] as 'MM'",
                default=_today.month,
                choices=[str(k) for k in range(1, 13)],
            )
            try:
                month = Month(year=_year, month=_month)
            except ValueError:
                logger.error("Invalid Month inputs %d %d", _year, _month)
                self._console.print(
                    "[red]Invalid month format.[/red] Please use YYYY-MM."
                )
                continue
            break
        return month

    def _collect_initial_balance(self) -> int:
        amount = IntPrompt.ask(
            "Enter initial [bold]balance amount[/bold] (integer)",
            default=0,
        )
        return amount

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

    def print_new_account_info(self, account_id: int, balance_id: int) -> None:
        """Print info about the newly created account and balance.

        Args:
            account_id (int): The ID of the created account.
            balance_id (int): The ID of the created balance.
        """
        account: Account | None = self._fetcher.get_account_by_id(account_id)
        balance: Balance | None = self._fetcher.get_balance_by_id(balance_id)
        if account is None or balance is None:
            _msg = "Error retrieving newly created account or balance."
            logger.error(_msg)
            self._console.print(f"[red]{_msg}[/red]")
            return

        self._console.print(
            f"\n[bold green]Account created successfully.[/bold green]\n"
            f"[yellow]Account name:[/yellow] {account.name}\n"
            f"[yellow]Account ID:[/yellow] {account.id}\n"
            f"[yellow]Description:[/yellow] {account.description}\n"
            f"[yellow]Currency:[/yellow] {account.currency_code}\n"
            f"[yellow]Category:[/yellow] {account.category_name}\n"
            f"[yellow]Initial month:[/yellow] {balance.month}\n"
            f"[yellow]Initial balance:[/yellow] {balance.amount}\n"
        )

    def validate_new_account(
        self, data: NewAccountData, account_id: int, balance_id: int
    ) -> bool:
        """Validate that the new account and balance were created correctly.

        Args:
            data (NewAccountData): The data used to create the account.
            account_id (int): The ID of the created account.
            balance_id (int): The ID of the created balance.

        Returns:
            bool: True if validation passes, False otherwise.
        """
        account = self._fetcher.get_account_by_id(account_id)
        balance = self._fetcher.get_balance_by_id(balance_id)

        def _log_and_print(message: str) -> None:
            logger.error(
                "Validation failed: " + message,
                extra={"account_id": account_id, "balance_id": balance_id},
            )
            self._console.print(
                "[magenta bold]Validation failed:[/magenta bold] " + message
            )

        if account is None:
            _log_and_print("Account not found.")
            return False
        if account.name != data.account_name:
            _log_and_print("Account name mismatch.")
            return False
        if account.description != data.description:
            _log_and_print("Account description mismatch.")
            return False
        if account.category_name != data.category_name:
            _log_and_print("Account category mismatch.")
            return False
        if account.currency_code != data.currency_code:
            _log_and_print("Account currency mismatch.")
            return False
        if account.status != data.status:
            _log_and_print("Account status mismatch.")
            return False

        if balance is None:
            _log_and_print("Balance not found.")
            return False
        if balance.account_id != account_id:
            _log_and_print("Balance account ID mismatch.")
            return False
        if str(balance.month) != str(data.initial_month):
            _log_and_print("Balance month mismatch.")
            return False
        if balance.amount != data.initial_amount:
            _log_and_print("Balance amount mismatch.")
            return False

        return True


def main() -> None:
    from dotenv import load_dotenv

    from nwtrack.bootstrap.logging_config import setup_logging

    load_dotenv()
    setup_logging()

    container = build_base_sqlite_uow_container()
    container.register(
        AccountCreator,
        lambda c: AccountCreator(uow=lambda: c.resolve(UnitOfWork)),
    )
    container.resolve(AccountCreator).run()


if __name__ == "__main__":
    main()
