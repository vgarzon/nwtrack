"""Create a balance entry interactively."""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import BalanceCreationPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Balance

logger = logging.getLogger(__name__)


class BalanceCreator:
    """Create one balance entry interactively."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        presenter: BalanceCreationPresenter,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self) -> OperationResult[tuple[int, int]]:
        """Run the balance creation workflow."""
        logger.info("Starting Balance Creator")
        self._presenter.show_header()

        active_accounts = self._fetcher.get_accounts(active_only=True)
        if not active_accounts:
            self._presenter.show_no_active_accounts()
            return OperationResult(success=False, error_message="No active accounts.")

        self._presenter.display_active_accounts(active_accounts)
        active_by_id = {account.id: account for account in active_accounts}

        account = self._select_account(active_by_id)
        if account is None:
            logger.warning("Balance creation cancelled at account selection.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        month = self._presenter.collect_month()
        if month is None:
            logger.warning("Balance creation cancelled at month selection.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        amount = self._presenter.collect_amount()
        if amount is None:
            logger.warning("Balance creation cancelled at amount entry.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Cancelled by user")

        balance = Balance(account_id=account.id, month=month, amount=amount)
        if not self._presenter.show_preview_and_confirm(account, balance):
            logger.warning("Balance creation declined by user.")
            self._presenter.show_cancellation("User declined.")
            return OperationResult(success=False, error_message="User declined")

        balance_id = self._create_balance(balance)
        if balance_id is None:
            _msg = "Balance creation failed."
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        self._presenter.show_success(account, balance)
        logger.info("Finished Balance Creator")
        return OperationResult(success=True, data=(account.id, balance_id))

    def _select_account(self, active_by_id: dict[int, Account]) -> Account | None:
        """Prompt until a valid active account is selected or cancelled."""
        while True:
            account_id = self._presenter.select_account()
            if account_id is None:
                return None
            account = active_by_id.get(account_id)
            if account is not None:
                return account
            self._presenter.show_account_not_found(account_id)

    def _create_balance(self, balance: Balance) -> int | None:
        """Insert the new balance row."""
        with self._uow() as uow:
            try:
                balance_id = uow.balances.insert(balance)
            except ValueError as exc:
                logger.exception("Error inserting balance: %s", exc)
                uow.rollback()
                return None
        return balance_id


def main() -> int:
    """Main entry point for balance creation script."""
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.bootstrap.composition import build_base_container
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.balance_presenters import (
        RichBalanceCreationPresenter,
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
        BalanceCreationPresenter,
        lambda c: RichBalanceCreationPresenter(console=c.resolve(Console)),
    ).register(
        BalanceCreator,
        lambda c: BalanceCreator(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(BalanceCreationPresenter),
        ),
    )

    result: OperationResult[tuple[int, int]] = container.resolve(BalanceCreator).run()
    return 0 if result.success else 1
