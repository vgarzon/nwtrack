"""
SQLite implementation of ExchangeRates repository.
"""

from __future__ import annotations

import logging

from nwtrack.application.ports.repos import BaseRepository
from nwtrack.domain.models import ExchangeRate
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class SQLiteExchangeRatesRepository(BaseRepository[ExchangeRate]):
    """Repository for exchange rates SQLite database operations."""

    def insert_many(self, data: list[ExchangeRate]) -> None:
        """Insert list of exchange rates into the exchange_rates table.

        Args:
            data (list[ExchangeRate]): List of ExchangeRate objects.
        """
        rowcount = self._db.execute_many(
            """
            INSERT INTO exchange_rates (currency, month, rate)
            VALUES (:currency, :month, :rate);
            """,
            [self._mapper.to_record(record) for record in data],
        )
        logger.info("Inserted %d exchange rate rows.", rowcount)

    def get(self, month: Month, currency_code: str) -> ExchangeRate | None:
        """Get the exchange rate for a specific currency code and month

        Args:
            month (Month): Month object
            currency_code (str): Currency code

        Returns:
            ExchangeRate | None: Exchange rate record if found, else None
        """
        query = """
        SELECT currency, month, rate FROM exchange_rates
        WHERE currency = :currency AND month = :month;
        """
        result = self._db.fetch_one(
            query, {"currency": currency_code, "month": str(month)}
        )
        if result:
            return self._mapper.to_entity(dict(result))
        else:
            return None

    def get_all(self) -> list[ExchangeRate]:
        """Get all exchange rate records.

        Returns:
            list[ExchangeRate]: List of all exchange rate records
        """
        query = "SELECT currency, month, rate FROM exchange_rates;"
        results = self._db.fetch_all(query)
        return [self._mapper.to_entity(dict(res)) for res in results]

    def get_currency(self, currency_code: str) -> list[ExchangeRate]:
        """Get exchange rates for a given currency code

        Args:
            currency_code (str): Currency code

        Returns:
            list[ExchangeRate]: List of exchange rate records
        """
        query = """
        SELECT currency, month, rate FROM exchange_rates
        WHERE currency = :currency;
        """
        results = self._db.fetch_all(query, {"currency": currency_code})
        return [self._mapper.to_entity(dict(res)) for res in results]

    def get_month(self, month: Month) -> list[ExchangeRate]:
        """Get exchange rates for all currencies for a given month

        Args:
            month (Month): Month object

        Returns:
            list[ExchangeRate]: List of exchange rate records
        """
        query = """
        SELECT currency, month, rate FROM exchange_rates
        WHERE month = :month;
        """
        results = self._db.fetch_all(query, {"month": str(month)})
        return [self._mapper.to_entity(dict(res)) for res in results]

    def count(self) -> int:
        """Count the number of exchange rate records.

        Returns:
            int: Number of exchange rage records.
        """
        query = "SELECT COUNT(*) AS cnt FROM exchange_rates;"
        result = self._db.fetch_one(query)
        return result["cnt"] if result else 0

    def delete_all(self) -> None:
        """Delete all category records."""
        query = "DELETE FROM exchange_rates;"
        cur = self._db.execute(query)
        logger.info("Deleted %d exchange rate records.", cur.rowcount)
