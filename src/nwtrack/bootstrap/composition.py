"""
Common dependency injection container setup for NWTrack application.
"""

from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.config.load import load_settings
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.domain.models import (
    Account,
    Balance,
    Category,
    Currency,
    ExchangeRate,
    NetWorth,
)
from nwtrack.infra.sqlite.repos.accounts import SQLiteAccountsRepository
from nwtrack.infra.sqlite.repos.balances import SQLiteBalancesRepository
from nwtrack.infra.sqlite.repos.categories import SQLiteCategoriesRepository
from nwtrack.infra.sqlite.repos.currencies import SQLiteCurrenciesRepository
from nwtrack.infra.sqlite.repos.exchange_rates import SQLiteExchangeRatesRepository
from nwtrack.infra.sqlite.repos.networth import SQLiteNetWorthRepository
from nwtrack.infra.sqlite.uow import SQLiteUnitOfWork
from nwtrack.mapper_registry import MapperRegistry
from nwtrack.mappers import (
    AccountMapper,
    BalanceMapper,
    CategoryMapper,
    CurrencyMapper,
    ExchangeRateMapper,
    NetWorthMapper,
)
from nwtrack.repo_registry import RepositoryRegistry, SQLiteRepositoryRegistry
from nwtrack.services import (
    AccountService,
    InitDataService,
    ReportService,
)

# TODO: Separate generic build functions from concrete repo implementations.


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


def build_base_sqlite_uow_container() -> Container:
    """Build base container with SQLite Unit of Work excluding services.

    Returns:
        Container: Configured DI container.
    """
    print("Setting dependency container with SQLite repos and Unit of Work.")
    # NOTE: Repo specs can be injected as an argument at composition time
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
        Settings,
        lambda _: load_settings(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        DBConnectionManager,
        lambda c: SQLiteConnectionManager(c.resolve(Settings)),
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
    )
    return container


def build_data_services_container(container: Container) -> Container:
    """Build basic data services container:

    Adds:
        - DBAdminService
        - InitDataService
        - ReportService
        - AccountService

    Args:
        container (Container): Base DI container.

    Returns:
        Container: DI container with additional services.
    """
    print("Setting up container with basic data and use case services.")
    container.register(
        DBAdminService,
        lambda c: SQLiteAdminService(
            c.resolve(Settings), c.resolve(DBConnectionManager)
        ),
    ).register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ReportService,
        lambda c: ReportService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        AccountService,
        lambda c: AccountService(uow=lambda: c.resolve(UnitOfWork)),
    )
    return container
