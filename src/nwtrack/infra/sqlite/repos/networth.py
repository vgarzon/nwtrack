"""
SQLite implementation of NetWorth repository.
"""

from __future__ import annotations

from nwtrack.dbmanager import DBConnectionManager
from nwtrack.domain.models import NetWorth
from nwtrack.domain.value_objects import Month
from nwtrack.mappers import NetWorthMapper


class SQLiteNetWorthRepository:
    """Repository net worth operations."""

    def __init__(self, db: DBConnectionManager, mapper: NetWorthMapper) -> None:
        self._db: DBConnectionManager = db
        self._mapper: NetWorthMapper = mapper

    def get(self, month: Month, currency_code: str = "USD") -> NetWorth:
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
        assert len(results) <= 1, "Expected at most one net worth record."
        return self._mapper.to_entity(dict(results[0]))

    def history(self, currency_code: str = "USD") -> list[NetWorth]:
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
