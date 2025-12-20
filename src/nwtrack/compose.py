"""
Common dependency injection container setup for NWTrack application.
"""

from nwtrack.config import Config, load_config
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.container import Container, Lifetime
from nwtrack.unitofwork import UnitOfWork, SQLiteUnitOfWork
from nwtrack.services import InitDataService, UpdateService, ReportService


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
        UnitOfWork,
        lambda c: SQLiteUnitOfWork(c.resolve(DBConnectionManager)),
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
