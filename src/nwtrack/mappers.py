"""
Mappers to convert records to and from entities.
"""

from __future__ import annotations
from typing import Protocol, Mapping, Any, TypeVar
from nwtrack.models import (
    Account,
    Balance,
    Currency,
    Category,
    ExchangeRate,
    Month,
    Side,
    Status,
)

TEntity = TypeVar("TEntity")


class Mapper(Protocol[TEntity]):
    """
    A mapper to convert records to and from entities.
    """

    def to_entity(self, record: Mapping[str, Any]) -> TEntity:
        """
        Convert a record to an entity.

        Args:
            record: The record to convert.

        Returns:
            The converted entity.
        """
        ...

    def to_record(self, entity: TEntity) -> Mapping[str, Any]:
        """
        Convert an entity to a record.

        Args:
            entity: The entity to convert.

        Returns:
            The converted record.
        """
        ...


class CurrencyMapper:
    """
    A mapper to convert currency records to and from currency entities.
    """

    def to_entity(self, record: Mapping[str, Any]) -> Currency:
        """
        Convert a currency record to a currency entity.

        Args:
            record: The currency record to convert.

        Returns:
            The converted currency entity.
        """
        return Currency(code=record["code"], description=record["description"])

    def to_record(self, entity: Currency) -> Mapping[str, Any]:
        """
        Convert a currency entity to a currency record.

        Args:
            entity: The currency entity to convert.

        Returns:
            The converted currency record.
        """
        return {
            "code": entity.code,
            "description": entity.description,
        }


class CategoryMapper:
    """
    A mapper to convert category records to and from category entities.
    """

    def to_entity(self, record: Mapping[str, Any]) -> Category:
        """
        Convert a category record to a category entity.

        Args:
            record: The category record to convert.

        Returns:
            The converted category entity.
        """
        return Category(name=record["name"], side=Side(record["side"]))

    def to_record(self, entity: Category) -> Mapping[str, Any]:
        """
        Convert a category entity to a category record.

        Args:
            entity: The category entity to convert.

        Returns:
            The converted category record.
        """
        return {
            "name": entity.name,
            "side": str(entity.side),
        }


class AccountMapper:
    """
    A mapper to convert account records to and from account entities.
    """

    def to_entity(self, record: Mapping[str, Any]) -> Account:
        """
        Convert an account record to an account entity.

        Args:
            record: The account record to convert.

        Returns:
            The converted account entity.
        """
        return Account(
            id=int(record.get("id", 0)),
            name=record["name"],
            description=record["description"],
            category_name=record["category"],
            currency_code=record["currency"],
            status=Status(record["status"]),
        )

    def to_record(self, entity: Account) -> Mapping[str, Any]:
        """
        Convert an account entity to an account record.

        Args:
            entity: The account entity to convert.

        Returns:
            The converted account record.
        """
        return {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description,
            "category": entity.category_name,
            "currency": entity.currency_code,
            "status": str(entity.status),
        }


class BalanceMapper:
    """
    A mapper to convert balance records to and from balance entities.
    """

    def to_entity(self, record: Mapping[str, Any]) -> Balance:
        """
        Convert a balance record to a balance entity.

        Args:
            record: The balance record to convert.

        Returns:
            The converted balance entity.
        """
        return Balance(
            id=int(record.get("id", 0)),
            account_id=int(record["account_id"]),
            month=Month.parse(record["month"]),
            amount=int(record["amount"]),
        )

    def to_record(self, entity: Balance) -> Mapping[str, Any]:
        """
        Convert a balance entity to a balance record.

        Args:
            entity: The balance entity to convert.

        Returns:
            The converted balance record.
        """
        return {
            "id": entity.id,
            "account_id": entity.account_id,
            "month": str(entity.month),
            "amount": entity.amount,
        }


class ExchangeRateMapper:
    """
    A mapper to convert exchange rate records to and from exchange rate entities.
    """

    def to_entity(self, record: Mapping[str, Any]) -> ExchangeRate:
        """
        Convert an exchange rate record to an exchange rate entity.

        Args:
            record: The exchange rate record to convert.

        Returns:
            The converted exchange rate entity.
        """
        return ExchangeRate(
            currency_code=record["currency"],
            month=Month.parse(record["month"]),
            rate=float(record["rate"]),
        )

    def to_record(self, entity: ExchangeRate) -> Mapping[str, Any]:
        """
        Convert an exchange rate entity to an exchange rate record.

        Args:
            entity: The exchange rate entity to convert.

        Returns:
            The converted exchange rate record.
        """
        return {
            "currency": entity.currency_code,
            "month": str(entity.month),
            "rate": entity.rate,
        }
