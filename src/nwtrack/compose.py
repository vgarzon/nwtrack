"""
Common dependency injection container setup for NWTrack application.
"""

from nwtrack.config import Config, load_config
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.services import NWTrackService
from nwtrack.admin import AdminService
from nwtrack.container import Container, Lifetime
from nwtrack.unitofwork import SQLiteUnitOfWork


def build_uow_container() -> Container:
    """Setup container with Unit of Work pattern implementation.

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
        SQLiteUnitOfWork,
        lambda c: SQLiteUnitOfWork(c.resolve(DBConnectionManager)),
    ).register(
        AdminService,
        lambda c: AdminService(c.resolve(Config), c.resolve(DBConnectionManager)),
    ).register(
        NWTrackService,
        lambda c: NWTrackService(uow=lambda: c.resolve(SQLiteUnitOfWork)),
    )
    return container
