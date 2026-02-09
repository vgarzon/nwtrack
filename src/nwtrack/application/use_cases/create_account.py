"""
Create new account interactively.
"""

import logging
from collections.abc import Callable

from nwtrack.application.dto import NewAccountData, OperationResult
from nwtrack.application.ports.presentation import AccountCreationPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Balance, Category

logger = logging.getLogger(__name__)


class AccountCreator:
    """Create account interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        presenter: AccountCreationPresenter,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self) -> OperationResult[tuple[int, int]]:
        """Run the account creation workflow.

        Returns:
            OperationResult with (account_id, balance_id) tuple if successful
        """
        logger.info("Starting Account Creator")

        # Show header and existing accounts
        self._presenter.show_header()
        accounts, categories_map = self._fetch_account_data(active_only=True)
        self._presenter.display_accounts(accounts, categories_map, active_only=True)

        # Collect account data
        data = self._presenter.collect_account_data()
        if data is None:
            logger.warning("Account creation cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        # Create account and balance
        res = self._create_account_and_balance(data)
        if res is None:
            _msg = "Account creation failed."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)
        account_id, balance_id = res

        # Get created entities for preview
        account = self._fetcher.get_account_by_id(account_id)
        balance = self._fetcher.get_balance_by_id(balance_id)
        if account is None or balance is None:
            _msg = "Error retrieving newly created account or balance."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        # Show preview and confirm
        if not self._presenter.show_preview_and_confirm(account, balance):
            logger.warning("Account creation cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="User declined")

        # Validate created account
        success, message = self._validate_created_account(data, account_id, balance_id)
        if not success:
            logger.error(
                "Validation failed: %s",
                message,
                extra={"account_id": account_id, "balance_id": balance_id},
            )
            self._presenter.show_error(f"Validation failed: {message}")
            return OperationResult(success=False, error_message=message)

        # Show success
        accounts, categories_map = self._fetch_account_data(active_only=False)
        self._presenter.show_success(accounts, categories_map)
        logger.info("Finished Account Creator")

        return OperationResult(success=True, data=(account_id, balance_id))

    def _create_account_and_balance(
        self, data: NewAccountData
    ) -> tuple[int, int] | None:
        """Create account and initial balance in the database.

        Args:
            data: Collected account data

        Returns:
            Tuple of account ID and balance ID, or None if failed
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

    def _fetch_account_data(
        self, active_only: bool = True
    ) -> tuple[list[Account], dict[int, Category | None]]:
        """Fetch accounts and their categories.

        Args:
            active_only: Whether to fetch only active accounts

        Returns:
            Tuple of accounts list and mapping of account IDs to categories
        """
        accounts = self._fetcher.get_accounts(active_only=active_only)
        categories_map = {
            account.id: self._fetcher.get_category_by_account_id(account.id)
            for account in accounts
        }
        return accounts, categories_map

    def _validate_created_account(
        self, data: NewAccountData, account_id: int, balance_id: int
    ) -> tuple[bool, str]:
        """Validate that the new account and balance were created correctly.

        Args:
            data: The data used to create the account
            account_id: The ID of the created account
            balance_id: The ID of the created balance

        Returns:
            Validation result and error message if any
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
    """Main entry point for account creation script."""
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.account_presenters import (
        RichAccountCreationPresenter,
    )

    load_dotenv()
    setup_logging()

    container = build_base_container()
    container.register(
        Console,
        lambda _: Console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichAccountCreationPresenter,
        lambda c: RichAccountCreationPresenter(
            console=c.resolve(Console),
            fetcher=c.resolve(FetchService),
        ),
    ).register(
        AccountCreator,
        lambda c: AccountCreator(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(RichAccountCreationPresenter),
        ),
    )

    result: OperationResult[tuple[int, int]] = container.resolve(AccountCreator).run()
    import sys

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
