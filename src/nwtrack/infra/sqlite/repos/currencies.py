"""
SQLite implementation of Currencies repository.
"""

from __future__ import annotations

import logging

from nwtrack.application.ports.repos import BaseRepository
from nwtrack.domain.models import Currency

logger = logging.getLogger(__name__)


class SQLiteCurrenciesRepository(BaseRepository[Currency]):
    """Repository for currencies SQLite database operations."""

    def insert_many(self, data: list[Currency]) -> None:
        """Insert list of currencies into the currencies table.

        Args:
            data (list[Currency]): List of Currency objects.
        """
        rowcount = self._db.execute_many(
            "INSERT INTO currencies (code, description) VALUES (:code, :description);",
            [self._mapper.to_record(entity) for entity in data],
        )
        logger.info("Inserted %d currency rows.", rowcount)

    def get(self, code: str) -> Currency | None:
        """Get currency by code.

        Args:
            code (str): Currency code.

        Returns:
            Currency | None: Currency record if found, else None.
        """
        query = "SELECT code, description FROM currencies WHERE code = :code;"
        result = self._db.fetch_one(query, {"code": code})
        if result:
            return self._mapper.to_entity(result)
        else:
            return None

    def get_codes(self) -> list[str]:
        """Get all currency codes.

        Returns:
            list[str]: List of currency codes.
        """
        query = "SELECT code FROM currencies;"
        results = self._db.fetch_all(query)
        currency_codes = [code for (code,) in results]
        return currency_codes

    def get_all(self) -> list[Currency]:
        """Get all currencies.

        Returns:
            list[Currency]: List of currency records.
        """
        query = "SELECT code, description FROM currencies;"
        results = self._db.fetch_all(query)
        currencies = [self._mapper.to_entity(record) for record in results]
        return currencies

    def get_dict(self) -> dict[str, Currency]:
        """Get all currencies in a dictionary indexed by code.

        Returns:
            dict[str, Currency]: Dictionary of currency records indexed by code.
        """
        results = self.get_all()
        currencies = {result.code: result for result in results}
        return currencies

    def count(self) -> int:
        """Count the number of currency records.

        Returns:
            int: Number of currency records.
        """
        query = "SELECT COUNT(*) AS cnt FROM currencies;"
        result = self._db.fetch_one(query)
        return result["cnt"] if result else 0

    def delete_all(self) -> None:
        """Delete all currency records."""
        query = "DELETE FROM currencies;"
        cur = self._db.execute(query)
        logger.info("Deleted %d currency records.", cur.rowcount)
