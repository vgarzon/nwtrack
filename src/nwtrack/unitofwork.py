"""
Unit of work pattern implementation for managing database transactions.
"""

from typing import Protocol

from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.repos import (
    AccountRepository,
    BalanceRepository,
    CategoryRepository,
    CurrencyRepository,
    ExchangeRateRepository,
    NetWorthRepository,
    SQLiteAccountRepository,
    SQLiteBalanceRepository,
    SQLiteCategoryRepository,
    SQLiteCurrencyRepository,
    SQLiteExchangeRateRepository,
    SQLiteNetWorthRepository,
)


class UnitOfWork(Protocol):
    """Unit of Work protocol for managing database transactions."""

    currencies: CurrencyRepository
    categories: CategoryRepository
    accounts: AccountRepository
    balances: BalanceRepository
    exchange_rates: ExchangeRateRepository
    net_worth: NetWorthRepository
    # _db: DBConnectionManager

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

    # currencies: SQLiteCurrencyRepository
    # categories: SQLiteCategoryRepository
    # accounts: SQLiteAccountRepository
    # balances: SQLiteBalanceRepository
    # exchange_rates: SQLiteExchangeRateRepository
    # net_worth: SQLiteNetWorthRepository
    # _db: SQLiteConnectionManager

    def __init__(self, db: SQLiteConnectionManager) -> None:
        """Initialize the Unit of Work with repository instances."""
        self._db = db

    def __enter__(self) -> "SQLiteUnitOfWork":
        """Enter the runtime context related to this object."""
        self.currencies = SQLiteCurrencyRepository(self._db)
        self.categories = SQLiteCategoryRepository(self._db)
        self.accounts = SQLiteAccountRepository(self._db)
        self.balances = SQLiteBalanceRepository(self._db)
        self.exchange_rates = SQLiteExchangeRateRepository(self._db)
        self.net_worth = SQLiteNetWorthRepository(self._db)
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
