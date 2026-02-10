"""
SQLAlchemy implementation of reporting queries.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nwtrack.application.dto import MonthlyCategoryBalance
from nwtrack.domain.value_objects import Month
from nwtrack.infra.persistence.orm.models import Account, Balance, Category, Side
from nwtrack.infra.persistence.orm.models import Category as CategoryModel

logger = logging.getLogger(__name__)


class ReportingQueries:
    """SQLAlchemy-based implementation of reporting queries.

    Provides aggregate queries for generating summary reports.
    """

    def __init__(self, session: Session):
        """Initialize reporting queries with SQLAlchemy session.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self._session = session

    def monthly_balance_total_by_category(
        self, month: Month
    ) -> list[MonthlyCategoryBalance]:
        """Get total balance amount by category name for a given month.

        Args:
            month: Month object

        Returns:
            List of MonthlyCategoryBalance DTOs with category and total amount.
        """
        stmt = (
            select(
                Category.name,
                Category.side,
                func.sum(Balance.amount).label("total_amount"),
            )
            .join(Account, Balance.account_id == Account.id)
            .join(Category, Account.category_name == Category.name)
            .where(Balance.month == month)
            .group_by(Category.name, Category.side)
            .order_by(Category.side, Category.name)
        )

        results = self._session.execute(stmt).all()

        return [
            MonthlyCategoryBalance(
                month=month,
                category=CategoryModel(name=row.name, side=Side(row.side)),
                amount=row.total_amount if row.total_amount is not None else 0,
            )
            for row in results
        ]
