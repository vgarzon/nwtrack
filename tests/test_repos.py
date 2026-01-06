"""
Test cases for repository management functionalities.
"""

import pytest
from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.infra.config.settings import Settings
from nwtrack.dbmanager import DBConnectionManager
from nwtrack.bootstrap.container import Container
from nwtrack.services import ReportService
from nwtrack.application.ports.uow import UnitOfWork
from tests.data.basic import TEST_DATA
from tests.helpers import _uow_factory, count_entries

# repo label, table name
REPO_MAPPING = [
    ("currencies", "currencies"),
    ("categories", "categories"),
    ("accounts", "accounts"),
    ("balances", "balances"),
    ("exchange_rates", "exchange_rates"),
]


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services for testing."""
    return base_container.register(
        DBAdminService,
        lambda c: SQLiteAdminService(
            c.resolve(Settings), c.resolve(DBConnectionManager)
        ),
    ).register(
        ReportService,
        lambda c: ReportService(uow=lambda: c.resolve(UnitOfWork)),
    )


def test_insert_hydrated(configured_container) -> None:
    """Test inserting hydrated objects."""
    admin_service: DBAdminService = configured_container.resolve(DBAdminService)
    admin_service.init_database()

    with _uow_factory(configured_container) as uow:
        for repo_name, table_name in REPO_MAPPING:
            repo = getattr(uow, repo_name)
            entities = repo.hydrate_many(TEST_DATA[table_name])
            repo.insert_many(entities)

    cnts = count_entries(configured_container)
    assert cnts["currencies"] == 3
    assert cnts["categories"] == 3
    assert cnts["accounts"] == 3
    assert cnts["balances"] == 9
    assert cnts["exchange_rates"] == 6


def test_delete_records(configured_container: Container) -> None:
    """Delete all records from all tables."""
    admin_service: DBAdminService = configured_container.resolve(DBAdminService)
    admin_service.init_database()
    reversed_repo_names = [repo_name for repo_name, _ in REPO_MAPPING][::-1]

    with _uow_factory(configured_container) as uow:
        for repo_name in reversed_repo_names:
            repo = getattr(uow, repo_name)
            repo.delete_all()

    cnts = count_entries(configured_container)
    for repo_name in reversed_repo_names:
        assert cnts[repo_name] == 0, f"Expected 0 records in {repo_name} repo"
