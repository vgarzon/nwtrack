"""
Transfer balance between accounts interactively.
"""

import logging
from collections.abc import Callable

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import BalanceTransferPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Balance, Side
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class BalanceTransfer:
    """Transfer funds between accounts for a selected month."""

    def __init__(
        self,
        uow: Callable[[], UnitOfWork],
        fetcher: FetchService,
        presenter: BalanceTransferPresenter,
    ) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        """Main entry point for balance transfer."""
        logger.info("Starting Balance Transfer")
        self._presenter.show_header()

        month = self._select_month()
        if month is None:
            self._presenter.show_cancellation()
            logger.warning("No month selected. Exiting.")
            return OperationResult(success=False, error_message="No month selected.")
        if not self._fetcher.check_month_in_balances(month):
            self._presenter.show_no_balances_warning(month)
            logger.warning("No balances found for %s. Stopping.", month)
            return OperationResult(
                success=False, error_message="No balances for selected month."
            )

        self.display_balances(month)

        from_account_id = self._presenter.select_from_account(month)
        if from_account_id is None:
            self._presenter.show_cancellation()
            logger.warning("No source account selected. Exiting.")
            return OperationResult(
                success=False, error_message="No source account selected."
            )

        to_account_id = self._presenter.select_to_account(month)
        if to_account_id is None:
            self._presenter.show_cancellation()
            logger.warning("No destination account selected. Exiting.")
            return OperationResult(
                success=False, error_message="No destination account selected."
            )

        if from_account_id == to_account_id:
            _msg = "Source and destination accounts must differ."
            logger.warning(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        from_account = self._fetcher.get_account_by_id(from_account_id)
        if from_account is None:
            _msg = f"Account {from_account_id} not found."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        to_account = self._fetcher.get_account_by_id(to_account_id)
        if to_account is None:
            _msg = f"Account {to_account_id} not found."
            logger.error(_msg)
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        amount = self._presenter.prompt_for_transfer_amount()

        from_delta, to_delta = self._compute_deltas(from_account, to_account, amount)

        self._presenter.show_transfer_preview(
            from_account, to_account, month, amount, from_delta, to_delta
        )

        if not self._presenter.prompt_to_confirm_transfer():
            _msg = "Transfer cancelled by user."
            self._presenter.show_cancellation()
            logger.warning(_msg)
            return OperationResult(success=False, error_message=_msg)

        if not self.execute_transfer(
            from_account_id, to_account_id, month, from_delta, to_delta
        ):
            _msg = "Failed to execute transfer."
            self._presenter.show_error(_msg)
            return OperationResult(success=False, error_message=_msg)

        self._presenter.show_success("Transfer completed successfully.")
        self.display_balances(month)

        logger.info("Finished Balance Transfer")
        return OperationResult(success=True)

    def _compute_deltas(
        self, from_account: Account, to_account: Account, amount: int
    ) -> tuple[int, int]:
        """Compute balance deltas based on account sides.

        The from-account always loses economic value; the to-account always gains it.
        Since liabilities are stored as positive amounts, "losing value" for a
        liability means its balance increases (more debt).

        Args:
            from_account: Source account
            to_account: Destination account
            amount: Transfer amount (positive)

        Returns:
            Tuple of (from_delta, to_delta) to apply to each account's balance
        """
        from_side = from_account.category.side
        to_side = to_account.category.side

        if from_side == Side.ASSET and to_side == Side.ASSET:
            return (-amount, +amount)
        elif from_side == Side.ASSET and to_side == Side.LIABILITY:
            return (-amount, -amount)
        elif from_side == Side.LIABILITY and to_side == Side.ASSET:
            return (+amount, +amount)
        else:  # LIABILITY -> LIABILITY
            return (+amount, -amount)

    def execute_transfer(
        self,
        from_account_id: int,
        to_account_id: int,
        month: Month,
        from_delta: int,
        to_delta: int,
    ) -> bool:
        """Execute the transfer atomically within a single UoW context.

        For each account, adjusts the existing balance by the delta.
        If no balance exists for the month, creates a new entry (treating missing as 0).

        Args:
            from_account_id: Source account ID
            to_account_id: Destination account ID
            month: Month to apply the transfer to
            from_delta: Amount to add to the from-account balance
            to_delta: Amount to add to the to-account balance

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._uow() as uow:
                for account_id, delta in (
                    (from_account_id, from_delta),
                    (to_account_id, to_delta),
                ):
                    try:
                        balance = uow.balances.get_by_account_id(month, account_id)
                        new_amount = balance.amount + delta
                        uow.balances.update(account_id, month, new_amount)
                    except IndexError:
                        # No balance for this account/month — treat missing as 0
                        new_amount = delta
                        uow.balances.insert(
                            Balance(
                                account_id=account_id, month=month, amount=new_amount
                            )
                        )
            return True
        except Exception as e:
            logger.exception("Error executing transfer: %s", e)
            return False

    def _select_month(self, n_months: int = 3) -> Month | None:
        """Select a month from recent months or input a specific month.

        Args:
            n_months: Number of recent months to display

        Returns:
            Selected Month object or None if quit
        """
        balance_counts = self._fetcher.get_balance_count_per_month()
        balance_counts.sort(key=lambda x: x[0], reverse=True)
        return self._presenter.select_month(balance_counts[:n_months])

    def display_balances(self, month: Month) -> None:
        """Display balance data for a given month.

        Args:
            month: Month object
        """
        balances = self._fetcher.get_month_balances(month, active_only=True)
        self._presenter.display_balances(balances, title_suffix=str(month))


def main() -> int:
    """Main entry point for balance transfer script.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    from dotenv import load_dotenv

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import build_base_container
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.balance_presenters import (
        RichBalanceTransferPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import Console, ConsoleSettings
    from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory

    load_dotenv()
    setup_logging()

    console_default = ConsoleSettings(record=False)

    container = build_base_container()
    container.register(
        Console,
        lambda _: ConsoleFactory(default_settings=console_default)(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        BalanceTransferPresenter,
        lambda c: RichBalanceTransferPresenter(console=c.resolve(Console)),
    ).register(
        BalanceTransfer,
        lambda c: BalanceTransfer(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(BalanceTransferPresenter),
        ),
    )
    result: OperationResult = container.resolve(BalanceTransfer).run()

    return 0 if result.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
