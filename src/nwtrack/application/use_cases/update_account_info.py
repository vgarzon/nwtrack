"""
Demo interactive use case for updating account information.
"""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult, UpdatedAccountData
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
        updated_account_data = self._presenter.collect_updated_data(current_account)
        if updated_account_data is None:
            logger.warning("Account update cancelled by user.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        # Show preview and confirm
        if not self._presenter.show_preview_and_confirm(updated_account_data):
            logger.warning("Account update cancelled by user.")
            self._presenter.show_cancellation("User declined.")
            return OperationResult(success=False, error_message="User declined")

        # Update in database
        updated_account = self._build_account(updated_account_data)
        self._update_account(updated_account, updated_account_data.tag_ids)

        # Verify update
        success = self._verify_update(account_id, updated_account, updated_account_data)
        if not success:
            _msg = "Account update verification failed."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        # Show success
        self._presenter.show_success()
        logger.info("Finished Account Updater")

        return OperationResult(success=True)

    def _build_account(self, update_data: UpdatedAccountData) -> Account:
        """Build an Account entity from update workflow input."""
        updated_account = Account(
            name=update_data.account_name,
            description=update_data.description,
            category_name=update_data.category_name,
            currency_code=update_data.currency_code,
            institution_id=update_data.institution_id,
            status=update_data.status,
        )
        updated_account.id = update_data.account_id
        return updated_account

    def _update_account(self, updated_account: Account, tag_ids: list[int]) -> None:
        """Update account data in the database.

        Args:
            updated_account: New account data
            tag_ids: Replacement tag assignments for the account
        """
        with self._uow() as uow:
            uow.accounts.update(updated_account)
            uow.tags.replace_for_account(updated_account.id, tag_ids)

    def _verify_update(
        self,
        account_id: int,
        update_data: Account,
        workflow_data: UpdatedAccountData,
    ) -> bool:
        """Verify that the account was updated correctly.

        Args:
            account_id: Account ID
            update_data: Updated account data
            workflow_data: Original workflow input including tag assignments

        Returns:
            True if update was successful, False otherwise
        """
        retrieved_data: Account | None = self._fetcher.get_account_by_id(account_id)
        if retrieved_data is None:
            logger.error("Error retrieving updated account.")
            return False
        if retrieved_data != update_data:
            return False
        expected_tag_ids = list(dict.fromkeys(workflow_data.tag_ids))
        stored_tag_ids = [
            tag.id for tag in self._fetcher.get_tags_for_account(account_id)
        ]
        return sorted(stored_tag_ids) == sorted(expected_tag_ids)


def main() -> None:
    """Main entry point for account update script."""
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.account_presenters import (
        RichAccountUpdatePresenter,
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
