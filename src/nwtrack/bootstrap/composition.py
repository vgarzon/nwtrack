"""
Common dependency injection container setup for NWTrack application.
"""

import logging

from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.ports.reporting import ReportingQueries
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.registries.mappers import MapperRegistry
from nwtrack.application.registries.repos import RepositoryRegistry
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.domain.models import (
    Account,
    Balance,
    Category,
    Currency,
    ExchangeRate,
    NetWorth,
)
from nwtrack.infra.config.load import load_settings
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.sqlite.db_manager import SQLiteConnectionManager
from nwtrack.infra.sqlite.mappers import (
    AccountMapper,
    BalanceMapper,
    CategoryMapper,
    CurrencyMapper,
    ExchangeRateMapper,
    NetWorthMapper,
)
from nwtrack.infra.sqlite.reporting import SQLiteReportingQueries
from nwtrack.infra.sqlite.repos.accounts import SQLiteAccountsRepository
from nwtrack.infra.sqlite.repos.balances import SQLiteBalancesRepository
from nwtrack.infra.sqlite.repos.categories import SQLiteCategoriesRepository
from nwtrack.infra.sqlite.repos.currencies import SQLiteCurrenciesRepository
from nwtrack.infra.sqlite.repos.exchange_rates import SQLiteExchangeRatesRepository
from nwtrack.infra.sqlite.repos.networth import SQLiteNetWorthRepository
from nwtrack.infra.sqlite.uow import SQLiteUnitOfWork

logger = logging.getLogger(__name__)

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


def build_sqlite_repo_registry(
    db: DBConnectionManager, mappers: MapperRegistry
) -> RepositoryRegistry:
    """Build a SQLite repository registry.

    Args:
        db_manager: Database connection manager.
        mappers: Mappers registry.

    Returns:
        The built SQLite repository registry.
    """
    # NOTE: Repo specs can be injected as an argument at composition time
    repo_specs = {
        "currencies": (Currency, SQLiteCurrenciesRepository),
        "categories": (Category, SQLiteCategoriesRepository),
        "accounts": (Account, SQLiteAccountsRepository),
        "balances": (Balance, SQLiteBalancesRepository),
        "exchange_rates": (ExchangeRate, SQLiteExchangeRatesRepository),
        "net_worth": (NetWorth, SQLiteNetWorthRepository),
    }
    return RepositoryRegistry(
        db=db,
        mappers=mappers,
        specs=repo_specs,
    )


def build_base_sqlite_uow_container() -> Container:
    """Build base container with SQLite Unit of Work excluding services.

    Returns:
        Container: Configured DI container.
    """
    logger.info("Setting dependency container with SQLite repos.")
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
        lambda c: build_sqlite_repo_registry(
            db=c.resolve(DBConnectionManager),
            mappers=c.resolve(MapperRegistry),
        ),
        lifetime=Lifetime.SINGLETON,
    ).register(
        ReportingQueries,
        lambda c: SQLiteReportingQueries(c.resolve(DBConnectionManager)),
        lifetime=Lifetime.SINGLETON,
    ).register(
        UnitOfWork,
        lambda c: SQLiteUnitOfWork(
            c.resolve(DBConnectionManager),
            c.resolve(MapperRegistry),
            c.resolve(RepositoryRegistry),
            c.resolve(ReportingQueries),
        ),
    )
    return container


def build_data_services_container(container: Container) -> Container:
    """Build basic data services container:

    Adds:
        - DBAdminService
        - InitDataService

    Args:
        container (Container): Base DI container.

    Returns:
        Container: DI container with additional services.
    """
    logger.info("Adding DB Admin and Init Data services to DI container.")
    container.register(
        DBAdminService,
        lambda c: DBAdminService(c.resolve(Settings), c.resolve(DBConnectionManager)),
    ).register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    )
    return container
