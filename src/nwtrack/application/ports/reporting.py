"""
Reporting related queries protocols
"""

from typing import Protocol

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    HistoryAggregationRequest,
    HistoryAggregationResult,
    MonthlyCategoryBalance,
    SingleMonthAggregationRequest,
    SingleMonthAggregationResult,
)
from nwtrack.domain.value_objects import Month


class ReportingQueries(Protocol):
    def get_available_aggregation_months(
        self,
        dimension: AggregationDimension,
        currency_code: str | None,
        status_scope: AccountStatusScope,
    ) -> list[Month]:
        """List distinct months with balances for one aggregation configuration."""
        ...

    def get_month_currencies(
        self, month: Month, status_scope: AccountStatusScope
    ) -> list[str]:
        """List distinct currencies for one month under a status filter."""
        ...

    def get_range_currencies(
        self,
        start_month: Month,
        end_month: Month,
        status_scope: AccountStatusScope,
    ) -> list[str]:
        """List distinct currencies across an inclusive month range."""
        ...

    def aggregate_single_month(
        self, request: SingleMonthAggregationRequest
    ) -> SingleMonthAggregationResult:
        """Group one month of balances by a supported aggregation dimension."""
        ...

    def aggregate_history(
        self,
        request: HistoryAggregationRequest,
    ) -> HistoryAggregationResult:
        """Group balances across an inclusive month range by one dimension."""
        ...

    def monthly_balance_total_by_category(
        self, month: Month
    ) -> list[MonthlyCategoryBalance]:
        """Get total balance amount by category name for a given moth.

        Args:
            month (Month): Month object
        Returns:
            list[MonthlyBalanceByCategory]: List of rows with category and total amount.
        """
        ...
