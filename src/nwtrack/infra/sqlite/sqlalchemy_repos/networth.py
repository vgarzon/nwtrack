"""
SQLAlchemy implementation of NetWorth repository.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from nwtrack.domain.value_objects import Month
from nwtrack.infra.sqlite.orm_models import NetWorth

logger = logging.getLogger(__name__)


class SQLAlchemyNetWorthRepository:
    """SQLAlchemy-based repository for net worth operations (read-only view)."""

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
        results = list(
            self._session.execute(
                select(NetWorth).where(
                    NetWorth.month == month, NetWorth.currency_code == currency_code
                )
            ).scalars()
        )

        if len(results) > 1:
            logger.error(
                "Multiple net worth records found for month %s and currency %s.",
                month,
                currency_code,
            )
            raise ValueError("Multiple net worth records found.")
        elif len(results) == 0:
            logger.info(
                "No net worth record found for month %s and currency %s.",
                month,
                currency_code,
            )
            return None

        try:
            return results[0]
        except Exception as e:
            logger.exception(
                "Error retrieving net worth record for month %s and currency %s: %s",
                month,
                currency_code,
                str(e),
            )
            raise ValueError("Error retrieving net worth record.") from e

    def get_history(self, currency_code: str = "USD") -> list[NetWorth]:
        """Get net worth history for a given currency.

        Args:
            currency_code: The currency code (defaults to "USD")

        Returns:
            List of Net Worth records
        """
        result = self._session.execute(
            select(NetWorth)
            .where(NetWorth.currency_code == currency_code)
            .order_by(NetWorth.month)
        ).scalars()
        return list(result)

    def get_last_n(self, n: int, currency_code: str = "USD") -> list[NetWorth]:
        """Get last n months of net worth history for a given currency.

        Args:
            n: Number of months to retrieve
            currency_code: The currency code (defaults to "USD")

        Returns:
            List of Net Worth records
        """
        result = self._session.execute(
            select(NetWorth)
            .where(NetWorth.currency_code == currency_code)
            .order_by(NetWorth.month.desc())
            .limit(n)
        ).scalars()
        results_list = list(result)

        if not results_list:
            logger.info("No net worth records found for currency %s.", currency_code)
            return []

        try:
            return results_list
        except Exception as e:
            logger.exception(
                "Error retrieving net worth records for currency %s: %s",
                currency_code,
                str(e),
            )
            return []
