"""
Create new account interactively.
"""

import logging
from collections.abc import Callable

from nwtrack.application.dto import NewAccountData
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Balance, Category, Status
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory
from nwtrack.entrypoints.cli.ui.prompts import (
    prompt_for_account_description,
    prompt_for_account_name,
    prompt_for_balance_amount,
    prompt_for_category_choice,
    prompt_for_currency_choice,
    prompt_for_month,
    prompt_for_status_choice,
    prompt_to_confirm_action,
)
from nwtrack.entrypoints.cli.ui.renderers import (
    build_accounts_table,
    build_currencies_table,
    build_indexed_categories_table,
    build_status_table,
    render_new_account_info,
)

logger = logging.getLogger(__name__)


class AccountCreator:
    """Create account interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        console_factory: ConsoleFactory,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._console = console_factory()

    def run(self) -> None:
        logger.info("Starting Account Creator")
        self._console.rule("[bold green]Account Creation[/bold green]")
        self.print_accounts(active_only=True)
        try:
            data = self.collect_data()
        except KeyboardInterrupt as e:
            self._console.print("[red]Account creation cancelled.[/red]", str(e))
            logger.warning("Account creation cancelled. %s", e)
            return

        res: tuple | None = self.create_account_and_balance(data)
        if res is None:
            _msg = "Account creation failed."
            logger.error(_msg)
            self._console.print(f"[red]{_msg}[/red]")
            return
        account_id, balance_id = res

        self._console.print("\n[bold green]New account data:[/bold green]")
        self.print_new_account_info(account_id, balance_id)
        proceed = prompt_to_confirm_action(self._console, "Create account?")
        if not proceed:
            self._console.print("[red]Account creation cancelled.[/red]")
            logger.warning("Account creation cancelled.")
            return

        success, message = self.validate_created_account(data, account_id, balance_id)
        if not success:
            logger.error(
                "Validation failed: %s",
                message,
                extra={"account_id": account_id, "balance_id": balance_id},
            )
            raise ValueError(f"New account validation failed: {message}")
            return

        self._console.print("[bold green]Account created successfully.[/bold green]")
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
            name = prompt_for_account_name(self._console)
            if name.lower() == "q":
                raise KeyboardInterrupt("Quit while collecting account name.")
            # TODO: Add string validation rules here
            if name:
                return name
            self._console.print(
                "[magenta]Account name cannot be empty.[/magenta] Please try again."
            )

    def _collect_description(self) -> str:
        description = prompt_for_account_description(self._console)
        if description.lower() == "q":
            raise KeyboardInterrupt("Quit while collecting description.")
        return description

    def _collect_category_name(self) -> str:
        categories = self._fetcher.get_all_categories()
        table = build_indexed_categories_table(categories)
        self._console.print(table)
        n_categories = len(categories)
        choice = prompt_for_category_choice(self._console, n_categories)
        if choice == 0:
            raise KeyboardInterrupt("Quit while collecting category name.")
        return categories[choice - 1].name

    def _collect_currency_code(self) -> str:
        currencies = self._fetcher.get_all_currencies()
        table = build_currencies_table(currencies)
        self._console.print(table)
        n_currencies = len(currencies)
        choice = prompt_for_currency_choice(self._console, n_currencies)
        if choice == 0:
            raise KeyboardInterrupt("Quit while collecting currency code.")
        return currencies[choice - 1].code

    def _collect_status(self) -> Status:
        status_options = [Status.ACTIVE, Status.INACTIVE]
        table = build_status_table(status_options)
        self._console.print(table)
        choice = prompt_for_status_choice(self._console, len(status_options))
        if choice == 0:
            raise KeyboardInterrupt("Quit while collecting account status.")
        return status_options[choice - 1]

    def _collect_initial_month(self) -> Month:
        """Input initial month from user.

        Returns:
            Month: Month object
        """
        return prompt_for_month(self._console)

    def _collect_initial_balance(self) -> int:
        return prompt_for_balance_amount(self._console)

    def print_accounts(self, active_only: bool = True) -> None:
        """Print accounts.

        Args:
            active_only (bool): Whether to print only active accounts.
        """
        accounts, category_map = self._fetch_account_data(active_only=active_only)
        title_prefix = "Active" if active_only else "All"
        table = build_accounts_table(accounts, category_map, title_prefix)
        self._console.print(table)

    def _fetch_account_data(
        self, active_only: bool = True
    ) -> tuple[list[Account], dict[int, Category | None]]:
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
        render_new_account_info(self._console, account, balance)

    def validate_created_account(
        self, data: NewAccountData, account_id: int, balance_id: int
    ) -> tuple[bool, str]:
        """Validate that the new account and balance were created correctly.

        Args:
            data (NewAccountData): The data used to create the account.
            account_id (int): The ID of the created account.
            balance_id (int): The ID of the created balance.

        Returns:
            tuple[bool, str]: validation result and error message if any.
        """
        account = self._fetcher.get_account_by_id(account_id)
        balance = self._fetcher.get_balance_by_id(balance_id)

        if account is None:
            return False, "Account not found."
        if account.name != data.account_name:
            return False, "Account name mismatch."
        if account.description != data.description:
            return False, "Account description mismatch."
        if account.category_name != data.category_name:
            return False, "Account category mismatch."
        if account.currency_code != data.currency_code:
            return False, "Account currency mismatch."
        if account.status != data.status:
            return False, "Account status mismatch."
        if balance is None:
            return False, "Balance not found."
        if balance.account_id != account_id:
            return False, "Balance account ID mismatch."
        if str(balance.month) != str(data.initial_month):
            return False, "Balance month mismatch."
        if balance.amount != data.initial_amount:
            return False, "Balance amount mismatch."

        return True, ""


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
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        AccountCreator,
        lambda c: AccountCreator(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            console_factory=c.resolve(ConsoleFactory),
        ),
    )
    container.resolve(AccountCreator).run()


if __name__ == "__main__":
    main()
