"""
Reporting module for generating summary reports from data analysis results.
"""

from nwtrack.application.dto import MonthlyCategoryBalance
from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.domain.models import Category, Side
from nwtrack.domain.value_objects import Month


class SQLiteReportingQueries:
    def __init__(self, db: DBConnectionManager) -> None:
        self._db: DBConnectionManager = db

    def monthly_balance_total_by_category(
        self, month: Month
    ) -> list[MonthlyCategoryBalance]:
        """Get total balance amount by category name for a given moth.

        Args:
            month (Month): Month object

        Returns:
            list[MonthlyCategoryBalance]: List of rows with category and total amount.
        """
        query = """
        SELECT
          c.name as category_name,
          c.side as category_side,
          sum(b.amount) as total_amount
        FROM
          balances b
        JOIN
          accounts a on b.account_id = a.id
        JOIN
          categories c on a.category = c.name
        WHERE
          b.month = :month
        GROUP by
          c.name, c.side
        ORDER by
          c.side, c.name;
        """
        rows = self._db.fetch_all(query, {"month": str(month)})
        results = []
        for row in rows:
            category_name = str(row["category_name"])
            category_side = str(row["category_side"])
            amount = int(row["total_amount"]) if row["total_amount"] is not None else 0
            assert row["category_name"] is not None
            category = Category(name=category_name, side=Side(category_side))
            results.append(
                MonthlyCategoryBalance(month=month, category=category, amount=amount)
            )
        return results
