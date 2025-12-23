"""
Unit of work pattern implementation for managing database transactions.
"""

from typing import Protocol

from nwtrack.dbmanager import SQLiteConnectionManager
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
from nwtrack.mappers import (
    AccountMapper,
    BalanceMapper,
    CategoryMapper,
    CurrencyMapper,
    ExchangeRateMapper,
    NetWorthMapper,
)


class UnitOfWork(Protocol):
    """Unit of Work protocol for managing database transactions."""

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

    def __init__(self, db: SQLiteConnectionManager) -> None:
        """Initialize the Unit of Work with repository instances."""
        self._db = db

    def __enter__(self) -> "SQLiteUnitOfWork":
        """Enter the runtime context related to this object."""
        self.currencies = SQLiteCurrenciesRepository(self._db, CurrencyMapper())
        self.categories = SQLiteCategoriesRepository(self._db, CategoryMapper())
        self.accounts = SQLiteAccountsRepository(self._db, AccountMapper())
        self.balances = SQLiteBalancesRepository(self._db, BalanceMapper())
        self.exchange_rates = SQLiteExchangeRatesRepository(
            self._db, ExchangeRateMapper()
        )
        self.net_worth = SQLiteNetWorthRepository(self._db, NetWorthMapper())
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
