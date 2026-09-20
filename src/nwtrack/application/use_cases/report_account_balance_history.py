"""CLI workflow for the single-account balance history report."""

from __future__ import annotations

import logging
from typing import Protocol

from nwtrack.application.dto import AccountBalanceHistoryResult, OperationResult
from nwtrack.application.ports.presentation import AccountBalanceHistoryPresenter
from nwtrack.domain.models import Account
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class _AccountHistoryFetchService(Protocol):
    """Read-only data needed to resolve an account for the CLI workflow."""

    def get_account_by_id(self, account_id: int) -> Account | None: ...

    def get_account_by_name(self, account_name: str) -> Account | None: ...


class _AccountBalanceHistoryRunner(Protocol):
    """Shared account balance history use-case dependency for the CLI workflow."""

    def run(
        self,
        account_id: int,
        start_month: Month,
        end_month: Month,
    ) -> OperationResult[AccountBalanceHistoryResult]: ...


class AccountBalanceHistoryReport:
    """CLI workflow for the single-account balance history report."""

    def __init__(
        self,
        fetcher: _AccountHistoryFetchService,
        history_report: _AccountBalanceHistoryRunner,
        presenter: AccountBalanceHistoryPresenter,
    ) -> None:
        self._fetcher = fetcher
        self._history_report = history_report
        self._presenter = presenter

    def run(
        self,
        start_month: Month,
        end_month: Month,
        account_id: int | None = None,
        account_name: str | None = None,
    ) -> OperationResult[AccountBalanceHistoryResult]:
        """Resolve the account, run the report, and drive the presenter."""
        logger.info("Starting account balance history report")
        self._presenter.show_header()

        resolved_account_id = self._resolve_account_id(account_id, account_name)
        if not resolved_account_id.success or resolved_account_id.data is None:
            error_message = resolved_account_id.error_message
            self._presenter.show_error(error_message)
            return OperationResult(success=False, error_message=error_message)

        result = self._history_report.run(
            resolved_account_id.data, start_month, end_month
        )
        if not result.success or result.data is None:
            error_message = (
                result.error_message or "Unable to build account balance history."
            )
            self._presenter.show_error(error_message)
            return OperationResult(success=False, error_message=error_message)

        if result.data.summary is None:
            self._presenter.show_no_data_message(result.data)
            return result

        self._presenter.display_account_balance_history(result.data)
        logger.info("Finished account balance history report")
        return result

    def _resolve_account_id(
        self,
        account_id: int | None,
        account_name: str | None,
    ) -> OperationResult[int]:
        if account_id is not None and account_name is not None:
            return OperationResult(
                success=False,
                error_message=(
                    "Provide either --account-id or --account-name, not both."
                ),
            )
        if account_id is not None:
            account = self._fetcher.get_account_by_id(account_id)
            if account is None:
                return OperationResult(
                    success=False,
                    error_message=f"Account {account_id} not found.",
                )
            return OperationResult(success=True, data=account.id)
        if account_name is not None:
            account = self._fetcher.get_account_by_name(account_name)
            if account is None:
                return OperationResult(
                    success=False,
                    error_message=f"Account '{account_name}' not found.",
                )
            return OperationResult(success=True, data=account.id)
        return OperationResult(
            success=False,
            error_message="Provide --account-id or --account-name.",
        )


def _parse_month(month: str) -> Month:
    return Month.parse(month)


def main(
    start_month: str,
    end_month: str,
    account_id: int | None = None,
    account_name: str | None = None,
) -> int:
    """Main entry point for the account balance history report."""
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.fetch import FetchService
    from nwtrack.application.use_cases.report_account_history import (
        ReportAccountBalanceHistory,
    )
    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.report_presenters import (
        RichAccountBalanceHistoryPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    load_dotenv()
    setup_logging()

    console = build_console()
    try:
        parsed_start_month = _parse_month(start_month)
        parsed_end_month = _parse_month(end_month)
    except ValueError:
        console.print("[error]Invalid month format. Please use YYYY-MM.[/error]")
        return 1

    container = build_base_container()
    container.register(
        Console,
        lambda _: console,
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ReportAccountBalanceHistory,
        lambda c: ReportAccountBalanceHistory(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichAccountBalanceHistoryPresenter,
        lambda c: RichAccountBalanceHistoryPresenter(console=c.resolve(Console)),
    ).register(
        AccountBalanceHistoryReport,
        lambda c: AccountBalanceHistoryReport(
            fetcher=c.resolve(FetchService),
            history_report=c.resolve(ReportAccountBalanceHistory),
            presenter=c.resolve(RichAccountBalanceHistoryPresenter),
        ),
    )

    result: OperationResult[AccountBalanceHistoryResult] = container.resolve(
        AccountBalanceHistoryReport
    ).run(
        start_month=parsed_start_month,
        end_month=parsed_end_month,
        account_id=account_id,
        account_name=account_name,
    )
    return 0 if result.success else 1
