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
)
from nwtrack.repo_registry import RepositoryRegistry
from nwtrack.mapper_registry import MapperRegistry


class UnitOfWork(Protocol):
    """Unit of Work protocol for managing database transactions."""

    currencies: CurrenciesRepository
    categories: CategoriesRepository
    accounts: AccountsRepository
    balances: BalancesRepository
    exchange_rates: ExchangeRatesRepository
    net_worth: NetWorthRepository

    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, exc_type, exc_value, traceback) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class SQLiteUnitOfWork:
    """Unit of Work protocol for managing SQLite database transactions."""

    def __init__(
        self,
        db: SQLiteConnectionManager,
        mappers: MapperRegistry,
        repo_registry: RepositoryRegistry,
    ) -> None:
        """Initialize the Unit of Work with repository instances."""
        self._db = db
        self._mappers = mappers
        self._repos = repo_registry

    def __enter__(self) -> "SQLiteUnitOfWork":
        """Enter the runtime context related to this object."""
        # NOTE: Exposing repositories directly for ease of use
        self.currencies = self._repos.currencies
        self.categories = self._repos.categories
        self.accounts = self._repos.accounts
        self.balances = self._repos.balances
        self.exchange_rates = self._repos.exchange_rates
        self.net_worth = self._repos.net_worth
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
