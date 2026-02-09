"""
Common dependency injection container setup for NWTrack application.
"""

import logging

from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.ports.reporting import ReportingQueries
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.infra.config.load import load_settings
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.sqlite.db_manager import SQLiteConnectionManager
from nwtrack.infra.sqlite.reporting import SQLiteReportingQueries
from nwtrack.infra.sqlite.sqlalchemy_manager import SQLAlchemySessionManager
from nwtrack.infra.sqlite.sqlalchemy_uow import SQLAlchemyUnitOfWork

logger = logging.getLogger(__name__)


def build_sqlalchemy_uow_container() -> Container:
    """Build container with SQLAlchemy Unit of Work.

    This is now the default container using SQLAlchemy ORM.

    Returns:
        Container: Configured DI container with SQLAlchemy
    """
    logger.info("Setting up dependency container with SQLAlchemy ORM.")
    container = Container()
    container.register(
        Settings,
        lambda _: load_settings(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        SQLAlchemySessionManager,
        lambda c: SQLAlchemySessionManager(c.resolve(Settings)),
        lifetime=Lifetime.SINGLETON,
    ).register(
        UnitOfWork,
        lambda c: SQLAlchemyUnitOfWork(
            lambda: c.resolve(SQLAlchemySessionManager).create_session()
        ),
    )
    return container


def build_base_container() -> Container:
    """Build base container - now uses SQLAlchemy by default.

    Returns:
        Container: Configured DI container
    """
    return build_sqlalchemy_uow_container()


# Legacy SQLite container (kept for backward compatibility during migration)
def build_legacy_sqlite_uow_container() -> Container:
    """Build legacy container with old SQLite Unit of Work.

    Deprecated: Use build_sqlalchemy_uow_container() instead.

    Returns:
        Container: Configured DI container with legacy implementation
    """
    logger.warning("Using legacy SQLite container - consider migrating to SQLAlchemy")
    from nwtrack.application.registries.mappers import MapperRegistry
    from nwtrack.application.registries.repos import RepositoryRegistry
    from nwtrack.domain.models import (
        Account,
        Balance,
        Category,
        Currency,
        ExchangeRate,
        NetWorth,
    )
    from nwtrack.infra.sqlite.mappers import (
        AccountMapper,
        BalanceMapper,
        CategoryMapper,
        CurrencyMapper,
        ExchangeRateMapper,
        NetWorthMapper,
    )
    from nwtrack.infra.sqlite.repos.accounts import SQLiteAccountsRepository
    from nwtrack.infra.sqlite.repos.balances import SQLiteBalancesRepository
    from nwtrack.infra.sqlite.repos.categories import SQLiteCategoriesRepository
    from nwtrack.infra.sqlite.repos.currencies import SQLiteCurrenciesRepository
    from nwtrack.infra.sqlite.repos.exchange_rates import (
        SQLiteExchangeRatesRepository,
    )
    from nwtrack.infra.sqlite.repos.networth import SQLiteNetWorthRepository
    from nwtrack.infra.sqlite.uow import SQLiteUnitOfWork

    def build_mapper_registry() -> MapperRegistry:
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
    """Build basic data services container.

    Adds:
        - DBAdminService (requires DBConnectionManager for DDL operations)
        - InitDataService

    Args:
        container: Base DI container

    Returns:
        Container: DI container with additional services
    """
    logger.info("Adding DB Admin and Init Data services to DI container.")

    # Register DBConnectionManager for DBAdminService if not already registered
    try:
        container.resolve(DBConnectionManager)
    except KeyError:
        container.register(
            DBConnectionManager,
            lambda c: SQLiteConnectionManager(c.resolve(Settings)),
            lifetime=Lifetime.SINGLETON,
        )

    container.register(
        DBAdminService,
        lambda c: DBAdminService(c.resolve(Settings), c.resolve(DBConnectionManager)),
    ).register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    )
    return container
