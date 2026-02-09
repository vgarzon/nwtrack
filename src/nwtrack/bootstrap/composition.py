"""
Common dependency injection container setup for NWTrack application.
"""

import logging

from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.infra.config.load import load_settings
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.sqlite.db_manager import SQLiteConnectionManager
from nwtrack.infra.sqlite.sqlalchemy_manager import SQLAlchemySessionManager
from nwtrack.infra.sqlite.sqlalchemy_uow import SQLAlchemyUnitOfWork

logger = logging.getLogger(__name__)


def build_sqlalchemy_uow_container() -> Container:
    """Build container with SQLAlchemy Unit of Work.

    This is now the default container using SQLAlchemy ORM.
    Also provides DBConnectionManager for legacy reporting queries.

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
        DBConnectionManager,
        lambda c: SQLiteConnectionManager(c.resolve(Settings)),
        lifetime=Lifetime.SINGLETON,
    ).register(
        SQLAlchemySessionManager,
        lambda c: SQLAlchemySessionManager(c.resolve(Settings)),
        lifetime=Lifetime.SINGLETON,
    ).register(
        UnitOfWork,
        lambda c: SQLAlchemyUnitOfWork(
            session_factory=lambda: c.resolve(
                SQLAlchemySessionManager
            ).create_session(),
            db_manager=c.resolve(DBConnectionManager),
        ),
    )
    return container


def build_base_container() -> Container:
    """Build base container - now uses SQLAlchemy by default.

    Returns:
        Container: Configured DI container
    """
    return build_sqlalchemy_uow_container()


def build_data_services_container(container: Container) -> Container:
    """Build basic data services container.

    Adds:
        - DBAdminService (requires SQLAlchemySessionManager for schema operations)
        - InitDataService

    Args:
        container: Base DI container

    Returns:
        Container: DI container with additional services
    """
    logger.info("Adding DB Admin and Init Data services to DI container.")

    container.register(
        DBAdminService,
        lambda c: DBAdminService(
            c.resolve(Settings), c.resolve(SQLAlchemySessionManager)
        ),
    ).register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    )
    return container
