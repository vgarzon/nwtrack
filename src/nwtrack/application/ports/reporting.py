"""
Reporting related queries protocols
"""

from typing import Protocol

from nwtrack.application.dto import MonthlyCategoryBalance
from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.domain.value_objects import Month


class ReportingQueries(Protocol):
    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

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
