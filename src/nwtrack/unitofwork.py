"""
Unit of work pattern implementation for managing database transactions.
"""

from typing import Protocol
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.repos import (
    AccountsRepository,
    BalancesRepository,
    CategoriesRepository,
    CurrenciesRepository,
    ExchangeRatesRepository,
    NetWorthRepository,
    SQLiteAccountsRepository,
    SQLiteBalancesRepository,
    SQLiteCategoriesRepository,
    SQLiteCurrenciesRepository,
    SQLiteExchangeRatesRepository,
    SQLiteNetWorthRepository,
)
from nwtrack.mappers import MapperRegistry


class UnitOfWork(Protocol):
    """Unit of Work protocol for managing database transactions."""

    _db: DBConnectionManager
    _mappers: MapperRegistry
    currencies: CurrenciesRepository
    categories: CategoriesRepository
    accounts: AccountsRepository
    balances: BalancesRepository
    exchange_rates: ExchangeRatesRepository
    net_worth: NetWorthRepository

    def __enter__(self) -> "UnitOfWork":
        """Enter the runtime context related to this object."""
        ...

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context related to this object."""
        ...

    def commit(self) -> None:
        """Commit the transaction."""
        ...

    def rollback(self) -> None:
        """Rollback the transaction."""
        ...


class SQLiteUnitOfWork:
    """Unit of Work protocol for managing SQLite database transactions."""

    def __init__(self, db: SQLiteConnectionManager, mappers: MapperRegistry) -> None:
        """Initialize the Unit of Work with repository instances."""
        self._db = db
        self._mappers = mappers

    def __enter__(self) -> "SQLiteUnitOfWork":
        """Enter the runtime context related to this object."""
        self.currencies = SQLiteCurrenciesRepository(self._db, self._mappers.currency)
        self.categories = SQLiteCategoriesRepository(self._db, self._mappers.category)
        self.accounts = SQLiteAccountsRepository(self._db, self._mappers.account)
        self.balances = SQLiteBalancesRepository(self._db, self._mappers.balance)
        self.exchange_rates = SQLiteExchangeRatesRepository(
            self._db, self._mappers.exchange_rate
        )
        self.net_worth = SQLiteNetWorthRepository(self._db, self._mappers.net_worth)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context related to this object."""
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        # NOTE: Connection closing is managed by SQLiteDBConnection singleton
        # self._db.close_connection()

    def commit(self) -> None:
        """Commit the transaction."""
        self._db.commit()

    def rollback(self) -> None:
        """Rollback the transaction."""
        self._db.rollback()
