"""
SQLAlchemy implementation of Currencies repository.
"""

from __future__ import annotations

import logging

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from nwtrack.application.ports.repos import CurrenciesRepository
from nwtrack.infra.sqlite.orm_models import Currency

logger = logging.getLogger(__name__)


class SQLAlchemyCurrenciesRepository(CurrenciesRepository):
    """SQLAlchemy-based repository for currencies operations."""

    def __init__(self, session: Session):
        """Initialize repository with SQLAlchemy session.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self._session = session

    def insert_many(self, data: list[Currency]) -> None:
        """Insert list of currencies into the currencies table.

        Args:
            data: List of Currency objects
        """
        self._session.add_all(data)
        self._session.flush()
        logger.info("Inserted %d currency rows.", len(data))

    def get(self, code: str) -> Currency | None:
        """Get currency by code.

        Args:
            code: Currency code

        Returns:
            Currency record if found, else None
        """
        return self._session.execute(
            select(Currency).where(Currency.code == code)
        ).scalar_one_or_none()

    def get_codes(self) -> list[str]:
        """Get all currency codes.

        Returns:
            List of currency codes
        """
        result = self._session.execute(select(Currency.code)).scalars()
        return list(result)

    def get_all(self) -> list[Currency]:
        """Get all currencies.

        Returns:
            List of currency records
        """
        result = self._session.execute(select(Currency)).scalars()
        return list(result)

    def get_dict(self) -> dict[str, Currency]:
        """Get all currencies in a dictionary indexed by code.

        Returns:
            Dictionary of currency records indexed by code
        """
        currencies = self.get_all()
        return {currency.code: currency for currency in currencies}

    def count(self) -> int:
        """Count the number of currency records.

        Returns:
            Number of currency records
        """
        result = self._session.execute(
            select(func.count()).select_from(Currency)
        ).scalar()
        return result or 0

    def delete_all(self) -> None:
        """Delete all currency records."""
        result = self._session.execute(delete(Currency))
        logger.info("Deleted %d currency records.", result.rowcount)

    def hydrate(self, record: dict) -> Currency:
        """Hydrate record to Currency entity.

        Args:
            record: Data dictionary

        Returns:
            Currency object
        """
        return Currency(code=record["code"], description=record["description"])

    def hydrate_many(self, data: list[dict]) -> list[Currency]:
        """Hydrate list of records to list of Currency entities.

        Args:
            data: List of data dictionaries

        Returns:
            List of Currency objects
        """
        return [self.hydrate(record) for record in data]
