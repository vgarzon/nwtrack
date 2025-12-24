"""
Common dependency injection container setup for NWTrack application.
"""

from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.config import Config, load_config
from nwtrack.container import Container, Lifetime
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.services import InitDataService, ReportService, UpdateService
from nwtrack.unitofwork import SQLiteUnitOfWork, UnitOfWork
from nwtrack.mappers import MapperRegistry, build_mapper_registry
from nwtrack.repo_registry import RepositoryRegistry, SQLiteRepositoryRegistry


def build_sqlite_uow_container() -> Container:
    """Setup container with SQLite Unit of Work pattern implementation.

    Returns:
        Container: Configured DI container.
    """
    print("Setting up dependency container with Unit of Work.")
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
            c.resolve(DBConnectionManager), c.resolve(MapperRegistry)
        ),
        lifetime=Lifetime.SINGLETON,
    ).register(
        UnitOfWork,
        lambda c: SQLiteUnitOfWork(
            c.resolve(DBConnectionManager), c.resolve(RepositoryRegistry)
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
