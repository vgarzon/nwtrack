"""
Reporting related queries protocols
"""

from typing import Protocol

from nwtrack.application.dto import (
    MonthlyCategoryBalance,
    SingleMonthAggregationRequest,
    SingleMonthAggregationResult,
)
from nwtrack.domain.value_objects import Month


class ReportingQueries(Protocol):
    def aggregate_single_month(
        self, request: SingleMonthAggregationRequest
    ) -> SingleMonthAggregationResult:
        """Group one month of balances by a supported aggregation dimension."""
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
