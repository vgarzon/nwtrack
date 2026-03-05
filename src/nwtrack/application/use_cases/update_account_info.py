"""
Demo interactive use case for updating account information.
"""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import AccountUpdatePresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account

logger = logging.getLogger(__name__)


class UpdateAccountInfo:
    """Update account information interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        presenter: AccountUpdatePresenter,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        """Run the account update workflow.

        Returns:
            OperationResult indicating success/failure
        """
        logger.info("Starting Update Account Info use case")

        # Show header and all accounts
        self._presenter.show_header()
        accounts = self._fetcher.get_accounts(active_only=False)
        self._presenter.display_accounts(accounts, active_only=False)

        # Select account to update
        account_id = self._presenter.select_account()
        if account_id is None:
            logger.warning("Account update cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        # Get current account data
        current_account = self._fetcher.get_account_by_id(account_id)
        if current_account is None:
            _msg = f"Account ID {account_id} not found."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        # Collect updated data
        updated_account = self._presenter.collect_updated_data(current_account)
        if updated_account is None:
            logger.warning("Account update cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        # Show preview and confirm
        if not self._presenter.show_preview_and_confirm(updated_account):
            logger.warning("Account update cancelled by user.")
            self._presenter.show_cancellation("User declined.")
            return OperationResult(success=False, error_message="User declined")

        # Update in database
        self._update_account(updated_account)

        # Verify update
        success = self._verify_update(account_id, updated_account)
        if not success:
            _msg = "Account update verification failed."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        # Show success
        self._presenter.show_success()
        logger.info("Finished Account Updater")

        return OperationResult(success=True)

    def _update_account(self, updated_account: Account) -> None:
        """Update account data in the database.

        Args:
            updated_account: New account data
        """
        with self._uow() as uow:
            uow.accounts.update(updated_account)

    def _verify_update(self, account_id: int, update_data: Account) -> bool:
        """Verify that the account was updated correctly.

        Args:
            account_id: Account ID
            update_data: Updated account data

        Returns:
            True if update was successful, False otherwise
        """
        retrieved_data: Account | None = self._fetcher.get_account_by_id(account_id)
        if retrieved_data is None:
            logger.error("Error retrieving updated account.")
            return False
        return retrieved_data == update_data


def main() -> None:
    """Main entry point for account update script."""
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.account_presenters import (
        RichAccountUpdatePresenter,
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
        RichAccountUpdatePresenter,
        lambda c: RichAccountUpdatePresenter(
            console=c.resolve(Console),
            fetcher=c.resolve(FetchService),
        ),
    ).register(
        UpdateAccountInfo,
        lambda c: UpdateAccountInfo(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(RichAccountUpdatePresenter),
        ),
    )

    result: OperationResult[None] = container.resolve(UpdateAccountInfo).run()
    import sys

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
