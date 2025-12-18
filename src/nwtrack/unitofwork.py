"""
Unit of work pattern implementation for managing database transactions.
"""

from nwtrack.dbmanager import DBConnectionManager
from nwtrack.repos import (
    SQLiteCurrencyRepository,
    SQLiteCategoryRepository,
    SQLiteExchangeRateRepository,
    SQLiteAccountRepository,
    SQLiteBalanceRepository,
    SQLiteNetWorthRepository,
)


class SQLiteUnitOfWork:
    """Unit of Work protocol for managing SQLite database transactions."""

    currency: SQLiteCurrencyRepository
    category: SQLiteCategoryRepository
    exchange_rate: SQLiteExchangeRateRepository
    account: SQLiteAccountRepository
    balance: SQLiteBalanceRepository
    net_worth: SQLiteNetWorthRepository

    def __init__(self, db: DBConnectionManager) -> None:
        """Initialize the Unit of Work with repository instances."""
        self._db = db

    def __enter__(self) -> "SQLiteUnitOfWork":
        """Enter the runtime context related to this object."""
        self.currency = SQLiteCurrencyRepository(self._db)
        self.category = SQLiteCategoryRepository(self._db)
        self.exchange_rate = SQLiteExchangeRateRepository(self._db)
        self.account = SQLiteAccountRepository(self._db)
        self.balance = SQLiteBalanceRepository(self._db)
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
