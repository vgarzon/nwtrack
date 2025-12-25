"""
Common dependency injection container setup for NWTrack application.
"""

from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.config import Config, load_config
from nwtrack.container import Container, Lifetime
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.mapper_registry import MapperRegistry
from nwtrack.mappers import (
    AccountMapper,
    BalanceMapper,
    CategoryMapper,
    CurrencyMapper,
    ExchangeRateMapper,
    NetWorthMapper,
)
from nwtrack.models import Account, Balance, Category, Currency, ExchangeRate, NetWorth
from nwtrack.repo_registry import RepositoryRegistry, SQLiteRepositoryRegistry
from nwtrack.repos import (
    SQLiteAccountsRepository,
    SQLiteBalancesRepository,
    SQLiteCategoriesRepository,
    SQLiteCurrenciesRepository,
    SQLiteExchangeRatesRepository,
    SQLiteNetWorthRepository,
)
from nwtrack.services import InitDataService, ReportService, UpdateService
from nwtrack.unitofwork import SQLiteUnitOfWork, UnitOfWork


def build_mapper_registry() -> MapperRegistry:
    """Build a mapper registry.

    Returns:
        The built mapper registry.
    """
    registry = MapperRegistry()
    registry.register(Currency, CurrencyMapper())
    registry.register(Category, CategoryMapper())
    registry.register(Account, AccountMapper())
    registry.register(Balance, BalanceMapper())
    registry.register(ExchangeRate, ExchangeRateMapper())
    registry.register(NetWorth, NetWorthMapper())
    return registry


def build_sqlite_uow_container() -> Container:
    """Setup container with SQLite Unit of Work pattern implementation.

    Returns:
        Container: Configured DI container.
    """
    print("Setting up dependency container with Unit of Work.")

    repo_specs = {
        "currencies": (Currency, SQLiteCurrenciesRepository),
        "categories": (Category, SQLiteCategoriesRepository),
        "accounts": (Account, SQLiteAccountsRepository),
        "balances": (Balance, SQLiteBalancesRepository),
        "exchange_rates": (ExchangeRate, SQLiteExchangeRatesRepository),
        "net_worth": (NetWorth, SQLiteNetWorthRepository),
    }
    container = Container()
    container.register(
        Config,
        lambda _: load_config(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        DBConnectionManager,
        lambda c: SQLiteConnectionManager(c.resolve(Config)),
        lifetime=Lifetime.SINGLETON,
    ).register(
        MapperRegistry,
        lambda _: build_mapper_registry(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        RepositoryRegistry,
        lambda c: SQLiteRepositoryRegistry(
            c.resolve(DBConnectionManager), c.resolve(MapperRegistry), repo_specs
        ),
        lifetime=Lifetime.SINGLETON,
    ).register(
        UnitOfWork,
        lambda c: SQLiteUnitOfWork(
            c.resolve(DBConnectionManager),
            c.resolve(MapperRegistry),
            c.resolve(RepositoryRegistry),
        ),
    ).register(
        DBAdminService,
        lambda c: SQLiteAdminService(c.resolve(Config), c.resolve(DBConnectionManager)),
    ).register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        UpdateService,
        lambda c: UpdateService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ReportService,
        lambda c: ReportService(uow=lambda: c.resolve(UnitOfWork)),
    )
    return container
