"""
SQLite implementation of NetWorth repository.
"""

from __future__ import annotations

import logging

from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.domain.models import NetWorth
from nwtrack.domain.value_objects import Month
from nwtrack.infra.sqlite.mappers import NetWorthMapper

logger = logging.getLogger(__name__)


class SQLiteNetWorthRepository:
    """Repository net worth operations."""

    def __init__(self, db: DBConnectionManager, mapper: NetWorthMapper) -> None:
        self._db: DBConnectionManager = db
        self._mapper: NetWorthMapper = mapper

    def get(self, month: Month, currency_code: str = "USD") -> NetWorth | None:
        """Get net worth value for given month and currency

        Args:
            month (Month): The month to query net worth.
            currency_code (str, optional): The currency code. Defaults to "USD".

        Returns:
            NetWorth: Net worth record.
        """
        query = """
        SELECT month, total_assets, total_liabilities, net_worth, currency
        FROM networth_history
        WHERE month = :month AND currency = :currency;
        """
        results = self._db.fetch_all(
            query, {"month": str(month), "currency": currency_code}
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
            networth = self._mapper.to_entity(dict(results[0]))
        except Exception as e:
            logger.exception(
                "Error mapping net worth record for month %s and currency %s: %s",
                month,
                currency_code,
                str(e),
            )
            raise ValueError("Error mapping net worth record.") from e
        return networth

    def get_history(self, currency_code: str = "USD") -> list[NetWorth]:
        """Get net worth history for a given currency.
        Args:
            currency_code (str, optional): The currency code. Defaults to "USD".

        Returns:
            list[NetWorth]: List of Net Worth records.
        """
        query = """
        SELECT month, total_assets, total_liabilities, net_worth, currency
        FROM networth_history
        WHERE currency = :currency
        ORDER BY month;
        """
        results = self._db.fetch_all(query, {"currency": currency_code})
        return [self._mapper.to_entity(dict(record)) for record in results]

    def get_last_n(self, n: int, currency_code: str = "USD") -> list[NetWorth]:
        """Get last n months of net worth history for a given currency.
        Args:
            n (int): Number of months to retrieve.
            currency_code (str, optional): The currency code. Defaults to "USD".

        Returns:
            list[NetWorth]: List of Net Worth records.
        """
        query = """
        SELECT month, total_assets, total_liabilities, net_worth, currency
        FROM networth_history
        WHERE currency = :currency
        ORDER BY month DESC
        LIMIT :n;
        """
        results = self._db.fetch_all(query, {"n": n, "currency": currency_code})
        if results is None:
            logger.info("No net worth records found for currency %s.", currency_code)
            return []
        try:
            last_n = [self._mapper.to_entity(dict(record)) for record in results]
        except Exception as e:
            logger.exception(
                "Error mapping net worth records for currency %s: %s",
                currency_code,
                str(e),
            )
            last_n = []
        return last_n
