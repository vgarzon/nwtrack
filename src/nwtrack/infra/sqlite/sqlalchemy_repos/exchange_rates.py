"""
SQLAlchemy implementation of ExchangeRates repository.
"""

from __future__ import annotations

import logging

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from nwtrack.application.ports.repos import ExchangeRatesRepository
from nwtrack.domain.value_objects import Month
from nwtrack.infra.sqlite.orm_models import ExchangeRate

logger = logging.getLogger(__name__)


class SQLAlchemyExchangeRatesRepository(ExchangeRatesRepository):
    """SQLAlchemy-based repository for exchange rates operations."""

    def __init__(self, session: Session):
        """Initialize repository with SQLAlchemy session.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self._session = session

    def insert_many(self, data: list[ExchangeRate]) -> None:
        """Insert list of exchange rates into the exchange_rates table.

        Args:
            data: List of ExchangeRate objects
        """
        self._session.add_all(data)
        self._session.flush()
        logger.info("Inserted %d exchange rate rows.", len(data))

    def get(self, month: Month, currency_code: str) -> ExchangeRate | None:
        """Get the exchange rate for a specific currency code and month.

        Args:
            month: Month object
            currency_code: Currency code

        Returns:
            Exchange rate record if found, else None
        """
        return self._session.execute(
            select(ExchangeRate).where(
                ExchangeRate.currency_code == currency_code,
                ExchangeRate.month == month,
            )
        ).scalar_one_or_none()

    def get_all(self) -> list[ExchangeRate]:
        """Get all exchange rate records.

        Returns:
            List of all exchange rate records
        """
        result = self._session.execute(select(ExchangeRate)).scalars()
        return list(result)

    def get_currency(self, currency_code: str) -> list[ExchangeRate]:
        """Get exchange rates for a given currency code.

        Args:
            currency_code: Currency code

        Returns:
            List of exchange rate records
        """
        result = self._session.execute(
            select(ExchangeRate).where(ExchangeRate.currency_code == currency_code)
        ).scalars()
        return list(result)

    def get_month(self, month: Month) -> list[ExchangeRate]:
        """Get exchange rates for all currencies for a given month.

        Args:
            month: Month object

        Returns:
            List of exchange rate records
        """
        result = self._session.execute(
            select(ExchangeRate).where(ExchangeRate.month == month)
        ).scalars()
        return list(result)

    def count(self) -> int:
        """Count the number of exchange rate records.

        Returns:
            Number of exchange rate records
        """
        result = self._session.execute(
            select(func.count()).select_from(ExchangeRate)
        ).scalar()
        return result or 0

    def delete_all(self) -> None:
        """Delete all exchange rate records."""
        result = self._session.execute(delete(ExchangeRate))
        logger.info("Deleted %d exchange rate records.", result.rowcount)

    def hydrate(self, record: dict) -> ExchangeRate:
        """Hydrate record to ExchangeRate entity.

        Args:
            record: Data dictionary

        Returns:
            ExchangeRate object
        """
        exchange_rate = ExchangeRate(
            currency_code=record["currency"],
            month=Month.parse(record["month"]) if isinstance(record["month"], str) else record["month"],
            rate=record["rate"],
        )
        # Set id after construction (init=False in ORM model)
        if "id" in record:
            exchange_rate.id = int(record["id"])
        return exchange_rate

    def hydrate_many(self, data: list[dict]) -> list[ExchangeRate]:
        """Hydrate list of records to list of ExchangeRate entities.

        Args:
            data: List of data dictionaries

        Returns:
            List of ExchangeRate objects
        """
        return [self.hydrate(record) for record in data]
