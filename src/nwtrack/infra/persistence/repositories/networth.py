"""
SQLAlchemy implementation of NetWorth repository.
"""

from __future__ import annotations

import logging

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from nwtrack.domain.value_objects import Month
from nwtrack.infra.persistence.orm.models import Account, Balance, Category, NetWorth

logger = logging.getLogger(__name__)


def _build_networth_query(session: Session):
    """Build the base networth aggregation query.

    This replaces the networth_history view with a SQLAlchemy query that:
    - Joins Balance -> Account -> Category
    - Aggregates by month and currency
    - Uses CASE expressions to sum assets and liabilities separately
    - Computes net worth as assets - liabilities

    Returns:
        SQLAlchemy select statement
    """
    total_assets = func.sum(
        case((Category.side == "asset", Balance.amount), else_=0)
    ).label("total_assets")

    total_liabilities = func.sum(
        case((Category.side == "liability", Balance.amount), else_=0)
    ).label("total_liabilities")

    net_worth = (
        func.sum(case((Category.side == "asset", Balance.amount), else_=0))
        - func.sum(case((Category.side == "liability", Balance.amount), else_=0))
    ).label("net_worth")

    return (
        select(
            Balance.month,
            Account.currency_code,
            total_assets,
            total_liabilities,
            net_worth,
        )
        .join(Account, Balance.account_id == Account.id)
        .join(Category, Account.category_name == Category.name)
        .group_by(Balance.month, Account.currency_code)
    )


class NetWorthRepository:
    """SQLAlchemy-based repository for net worth operations.

    Computes net worth by aggregating balance data through Account and Category joins.
    This replaces the previous approach of querying the networth_history view.
    """

    def __init__(self, session: Session):
        """Initialize repository with SQLAlchemy session.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self._session = session

    def get(self, month: Month, currency_code: str = "USD") -> NetWorth | None:
        """Get net worth value for given month and currency.

        Args:
            month: The month to query net worth
            currency_code: The currency code (defaults to "USD")

        Returns:
            Net worth record, or None if not found
        """
        query = _build_networth_query(self._session).where(
            Balance.month == month, Account.currency_code == currency_code
        )

        result = self._session.execute(query).one_or_none()

        if result is None:
            logger.info(
                "No net worth record found for month %s and currency %s.",
                month,
                currency_code,
            )
            return None

        try:
            # Unpack result row into NetWorth DTO
            return NetWorth(
                month=result.month,
                currency_code=result.currency_code,
                assets=result.total_assets,
                liabilities=result.total_liabilities,
                net_worth=result.net_worth,
            )
        except Exception as e:
            logger.exception(
                "Error constructing net worth record for month %s and currency %s: %s",
                month,
                currency_code,
                str(e),
            )
            raise ValueError("Error constructing net worth record.") from e

    def get_history(self, currency_code: str = "USD") -> list[NetWorth]:
        """Get net worth history for a given currency.

        Args:
            currency_code: The currency code (defaults to "USD")

        Returns:
            List of Net Worth records
        """
        query = (
            _build_networth_query(self._session)
            .where(Account.currency_code == currency_code)
            .order_by(Balance.month)
        )

        results = self._session.execute(query).all()

        return [
            NetWorth(
                month=row.month,
                currency_code=row.currency_code,
                assets=row.total_assets,
                liabilities=row.total_liabilities,
                net_worth=row.net_worth,
            )
            for row in results
        ]

    def get_last_n(self, n: int, currency_code: str = "USD") -> list[NetWorth]:
        """Get last n months of net worth history for a given currency.

        Args:
            n: Number of months to retrieve
            currency_code: The currency code (defaults to "USD")

        Returns:
            List of Net Worth records (most recent first)
        """
        query = (
            _build_networth_query(self._session)
            .where(Account.currency_code == currency_code)
            .order_by(Balance.month.desc())
            .limit(n)
        )

        results = self._session.execute(query).all()

        if not results:
            logger.info("No net worth records found for currency %s.", currency_code)
            return []

        try:
            return [
                NetWorth(
                    month=row.month,
                    currency_code=row.currency_code,
                    assets=row.total_assets,
                    liabilities=row.total_liabilities,
                    net_worth=row.net_worth,
                )
                for row in results
            ]
        except Exception as e:
            logger.exception(
                "Error constructing net worth records for currency %s: %s",
                currency_code,
                str(e),
            )
            return []
