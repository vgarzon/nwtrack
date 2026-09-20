"""Shared single-account balance history use case."""

from __future__ import annotations

from collections.abc import Callable

from nwtrack.application.dto import (
    AccountBalanceHistoryResult,
    AccountBalanceHistoryRow,
    AccountBalanceHistorySummary,
    OperationResult,
)
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.domain.value_objects import Month


def _month_in_range(month: Month, start_month: Month, end_month: Month) -> bool:
    return not (month < start_month) and not (end_month < month)


class ReportAccountBalanceHistory:
    """Run one account's balance history query across an inclusive month range."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow

    def run(
        self,
        account_id: int,
        start_month: Month,
        end_month: Month,
    ) -> OperationResult[AccountBalanceHistoryResult]:
        """Validate the request and return one account's balance history.

        Gap months (no balance record) are returned with a null balance and
        a null delta. Delta is computed against the last month that actually
        had a balance record, skipping over any gaps. Summary trend stats are
        computed only over months with an actual balance record.
        """
        if end_month < start_month:
            return OperationResult(
                success=False,
                error_message=(
                    "Start month must be earlier than or equal to end month."
                ),
            )

        with self._uow() as uow:
            account = uow.accounts.get_by_id(account_id)
            if account is None:
                return OperationResult(
                    success=False,
                    error_message=f"Account {account_id} not found.",
                )

            balances_by_month = {
                balance.month: balance.amount
                for balance in uow.balances.get_all_by_account_id(account_id)
                if _month_in_range(balance.month, start_month, end_month)
            }

            account_name = account.name
            category_name = account.category_name
            currency_code = account.currency_code
            institution_name = (
                account.institution.name if account.institution else None
            )

        rows: list[AccountBalanceHistoryRow] = []
        actual_months: list[Month] = []
        actual_amounts: list[int] = []
        last_actual_amount: int | None = None

        month = start_month
        while True:
            amount = balances_by_month.get(month)
            if amount is None:
                rows.append(
                    AccountBalanceHistoryRow(month=month, balance=None, delta=None)
                )
            else:
                delta = (
                    amount - last_actual_amount
                    if last_actual_amount is not None
                    else None
                )
                rows.append(
                    AccountBalanceHistoryRow(month=month, balance=amount, delta=delta)
                )
                last_actual_amount = amount
                actual_months.append(month)
                actual_amounts.append(amount)
            if month == end_month:
                break
            month = month.increment()

        summary: AccountBalanceHistorySummary | None = None
        if actual_amounts:
            summary = AccountBalanceHistorySummary(
                min_balance=min(actual_amounts),
                max_balance=max(actual_amounts),
                average_balance=sum(actual_amounts) / len(actual_amounts),
                total_change=actual_amounts[-1] - actual_amounts[0],
                first_month=actual_months[0],
                last_month=actual_months[-1],
            )

        result = AccountBalanceHistoryResult(
            account_id=account_id,
            account_name=account_name,
            category_name=category_name,
            currency_code=currency_code,
            institution_name=institution_name,
            start_month=start_month,
            end_month=end_month,
            rows=rows,
            summary=summary,
        )
        return OperationResult(success=True, data=result)
