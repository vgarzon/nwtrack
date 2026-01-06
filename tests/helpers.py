"""
Halper functions to initialize the database with sample data.
"""

from nwtrack.admin import DBAdminService
from nwtrack.bootstrap.container import Container
from nwtrack.services import InitDataService
from nwtrack.application.ports.uow import UnitOfWork


def init_db_tables_w_entities(container: Container, entities: dict[str, list]) -> None:
    """Initialize database and load sample data."""
    container.resolve(DBAdminService).init_database()
    data_svc: InitDataService = container.resolve(InitDataService)
    data_svc._insert_entities(entities)


def init_db_tables_from_csv(container: Container, file_paths: dict[str, str]) -> None:
    """Initialize database and load sample data."""
    container.resolve(DBAdminService).init_database()
    data_svc: InitDataService = container.resolve(InitDataService)
    data_svc.insert_data_from_csv(file_paths)


def _uow_factory(container: Container) -> UnitOfWork:
    return container.resolve(UnitOfWork)


def count_entries(container: Container) -> dict[str, int]:
    """Count entries from all repos."""
    # TODO: refactor to use RepoRegistry (pending)
    repo_labels = [
        "currencies",
        "categories",
        "accounts",
        "balances",
        "exchange_rates",
    ]
    with _uow_factory(container) as uow:
        counts = {}
        for label in repo_labels:
            repo = getattr(uow, label)
            count = repo.count()
            counts[label] = count
    return counts
