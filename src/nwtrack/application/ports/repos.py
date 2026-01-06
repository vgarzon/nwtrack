"""
Repository protocols.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, Generic

from nwtrack.dbmanager import DBConnectionManager
from nwtrack.domain.models import (
    Account,
    Balance,
    Category,
    Currency,
    ExchangeRate,
    NetWorth,
)
from nwtrack.domain.value_objects import Month
from nwtrack.application.ports.mappers import Mapper, SQLiteRecord

TEntity = TypeVar("TEntity")


class Repository(Protocol[TEntity]):
    """Generic repository protocol."""

    def insert_many(self, data: list[TEntity]) -> None: ...

    def get_all(self) -> list[TEntity]: ...

    def count(self) -> int: ...

    def delete_all(self) -> None: ...

    def hydrate(self, data: SQLiteRecord) -> TEntity: ...

    def hydrate_many(self, data: list[SQLiteRecord]) -> list[TEntity]: ...


class BaseRepository(Generic[TEntity]):
    """Base repository class implementing common methods."""

    def __init__(self, db: DBConnectionManager, mapper: Mapper[TEntity]) -> None:
        self._db: DBConnectionManager = db
        self._mapper: Mapper = mapper

    def insert_many(self, data: list[TEntity]) -> None:
        """Insert list of entities into the corresponding table.

        Args:
            data (list[Entity]): List of entity objects.
        """
        raise NotImplementedError

    def get_all(self) -> list[TEntity]:
        """Get all entities.

        Returns:
            list[Entity]: List of entity objects.
        """
        raise NotImplementedError

    def count(self) -> int:
        """Count the number of records.

        Returns:
            int: Number of records.
        """
        raise NotImplementedError

    def delete_all(self) -> None:
        """Delete all records."""
        raise NotImplementedError

    def hydrate(self, record: dict) -> TEntity:
        """Hydrate record to Entity.

        Args:
            record (dict): data dictionary

        Returns:
            Entity: Entity object.
        """
        return self._mapper.to_entity(record)

    def hydrate_many(self, data: list[dict]) -> list[TEntity]:
        """Hydrate list of records to list of Entities.

        Args:
            data (list[dict]): list of data dictionaries.

        Returns:
            list[Entity]: list of Entity objects.
        """
        return [self.hydrate(record) for record in data]


class CurrenciesRepository(Repository[Currency], Protocol):
    """Protocol for currency repository operations."""

    def get(self, code: str) -> Currency | None:
        """Get currency by code."""
        ...

    def get_codes(self) -> list[str]:
        """Get all currency codes."""
        ...

    def get_dict(self) -> dict[str, Currency]:
        """Get all currencies in a dictionary indexed by code."""
        ...


class CategoriesRepository(Repository[Category], Protocol):
    """Protocol for category repository operations."""

    def get(self, name: str) -> Category | None:
        """Get category by name."""
        ...

    def get_dict(self) -> dict[str, Category]:
        """Get all categories in a dictionary indexed by name."""
        ...


class ExchangeRatesRepository(Repository[ExchangeRate], Protocol):
    """Protocol for exchange rate repository operations."""

    def get(self, month: Month, currency_code: str) -> ExchangeRate | None:
        """Get the exchange rate for a specific currency code and month."""
        ...

    def get_currency(self, currency_code: str) -> list[ExchangeRate]:
        """Get exchange rates for a given currency code."""
        ...

    def get_month(self, month: Month) -> list[ExchangeRate]:
        """Get exchange rates for all currencies for a given month."""
        ...


class AccountsRepository(Repository[Account], Protocol):
    """Protocol for account repository operations."""

    def get_by_id(self, account_id: int) -> Account | None:
        """Get account by ID."""
        ...

    def get_by_name(self, account_name: str) -> Account | None:
        """Get account by name."""
        ...

    def get_active(self) -> list[Account]:
        """Get all active accounts."""
        ...

    def get_dict_id(self) -> dict[int, Account]:
        """Get all accounts in a dictionary indexed by account id."""
        ...

    def get_dict_name(self) -> dict[str, Account]:
        """Get all accounts in a dictionary indexed by name."""
        ...

    def insert(self, data: Account) -> int:
        """Insert account object in respective table."""
        ...

    def delete_by_id(self, account_id: int) -> int:
        """Delete account by ID."""
        ...

    def update_name(self, account_id: int, new_name: str) -> int:
        """Update account name."""
        ...

    def update_status(self, account_id: int, new_status: str) -> int:
        """Update account status."""
        ...

    def update_currency(self, account_id: int, new_currency_code: str) -> int:
        """Update account currency."""
        ...

    def update_category(self, account_id: int, new_category_name: str) -> int:
        """Update account category."""
        ...

    def update_description(self, account_id: int, new_description: str) -> int:
        """Update account description."""
        ...


class BalancesRepository(Repository[Balance], Protocol):
    """Protocol for balance repository operations."""

    def insert(self, data: Balance) -> int:
        """Insert balance object in respective table."""
        ...

    def get(self, month: Month, account_name: str) -> Balance:
        """Get all account balances on a specific month."""
        ...

    def get_by_id(self, balance_id: int) -> Balance | None:
        """Get balance by ID."""
        ...

    def get_by_account_id(self, month: Month, account_id: int) -> Balance:
        """Get all balances given account id and month."""
        ...

    def get_all_by_account_id(self, account_id: int) -> list[Balance]:
        """Get all balances given account id."""
        ...

    def get_month(self, month: Month, active_only: bool = True) -> list[Balance]:
        """Get all account balances on a specific month."""
        ...

    def update(self, account_id: int, month: Month, new_amount: int) -> None:
        """Update the balance for specific account and month."""
        ...

    def check_month(self, month: Month):
        """Check that there are balance entries for a given month."""
        ...

    def roll_forward(self, month: Month) -> None:
        """Roll account balances forward from one month to the next."""
        ...

    def fetch_sample(self, limit: int = 5) -> list[Balance]:
        """Fetch sample balance records for debugging."""
        ...

    def delete_by_account_id(self, account_id: int) -> int:
        """Delete balance records by account ID."""
        ...

    def count_per_month(self) -> list[tuple[Month, int]]:
        """Count the number balance entries per month."""
        ...

    def copy_by_month(self, from_month: Month, to_month: Month) -> int:
        """Copy balance entries from one month to another."""
        ...


class NetWorthRepository(Protocol):
    """Protocol for net worth repository operations."""

    def get(self, month: Month, currency_code: str = "USD") -> NetWorth:
        """Get net worth value for given month and currency."""
        ...

    def history(self, currency_code: str = "USD") -> list[NetWorth]:
        """Get net worth history for a given currency."""
        ...
