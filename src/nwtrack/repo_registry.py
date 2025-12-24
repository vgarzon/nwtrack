"""
Repository Registry.

Collects repositories and mappers.  Passsed to Unit of Work in composition root.
"""

from typing import Protocol
from nwtrack.repos import (
    CurrenciesRepository,
    CategoriesRepository,
    AccountsRepository,
    BalancesRepository,
    ExchangeRatesRepository,
    NetWorthRepository,
    SQLiteCurrenciesRepository,
    SQLiteCategoriesRepository,
    SQLiteAccountsRepository,
    SQLiteBalancesRepository,
    SQLiteExchangeRatesRepository,
    SQLiteNetWorthRepository,
)
from nwtrack.mappers import MapperRegistry
from nwtrack.dbmanager import DBConnectionManager


class RepositoryRegistry(Protocol):
    """Repository Registry protocol for accessing repositories."""

    _db: DBConnectionManager
    _mappers: MapperRegistry
    currencies: CurrenciesRepository
    categories: CategoriesRepository
    accounts: AccountsRepository
    balances: BalancesRepository
    exchange_rates: ExchangeRatesRepository
    net_worth: NetWorthRepository


class SQLiteRepositoryRegistry:
    """Registry for all repositories."""

    _db: DBConnectionManager
    _mappers: MapperRegistry
    currencies: SQLiteCurrenciesRepository
    categories: SQLiteCategoriesRepository
    accounts: SQLiteAccountsRepository
    balances: SQLiteBalancesRepository
    exchange_rates: SQLiteExchangeRatesRepository
    net_worth: SQLiteNetWorthRepository

    def __init__(self, db: DBConnectionManager, mappers: MapperRegistry):
        """Initialize the Repository Registry with repository instances."""
        self._db = db
        self._mappers = mappers
        self.currencies = SQLiteCurrenciesRepository(db, mappers.currency)
        self.categories = SQLiteCategoriesRepository(db, mappers.category)
        self.accounts = SQLiteAccountsRepository(db, mappers.account)
        self.balances = SQLiteBalancesRepository(db, mappers.balance)
        self.exchange_rates = SQLiteExchangeRatesRepository(db, mappers.exchange_rate)
        self.net_worth = SQLiteNetWorthRepository(db, mappers.net_worth)
