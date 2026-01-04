"""
Test cases for repository management functionalities.
"""

from nwtrack.admin import DBAdminService
from nwtrack.compose import build_data_services_container
from nwtrack.container import Container
from nwtrack.services import ReportService
from nwtrack.unitofwork import UnitOfWork
from tests.data.basic import TEST_DATA

# repo label, table name
REPO_MAPPING = [
    ("currencies", "currencies"),
    ("categories", "categories"),
    ("accounts", "accounts"),
    ("balances", "balances"),
    ("exchange_rates", "exchange_rates"),
]


def count_entries(test_container: Container) -> dict[str, int]:
    """Count entries from all repos."""
    container = build_data_services_container(test_container)
    prn_svc: ReportService = container.resolve(ReportService)

    return prn_svc.count_entries()


def uow_factory(container: Container) -> UnitOfWork:
    return container.resolve(UnitOfWork)


def test_insert_hydrated(test_container) -> None:
    """Test inserting hydrated objects."""
    container = build_data_services_container(test_container)
    admin_service: DBAdminService = container.resolve(DBAdminService)
    admin_service.init_database()

    with uow_factory(container) as uow:
        for repo_name, table_name in REPO_MAPPING:
            repo = getattr(uow, repo_name)
            entities = repo.hydrate_many(TEST_DATA[table_name])
            repo.insert_many(entities)

    cnts = count_entries(test_container)
    assert cnts["currencies"] == 3
    assert cnts["categories"] == 3
    assert cnts["accounts"] == 3
    assert cnts["balances"] == 9
    assert cnts["exchange_rates"] == 6


def test_delete_records(test_container: Container) -> None:
    """Delete all records from all tables."""
    container = build_data_services_container(test_container)
    admin_service: DBAdminService = container.resolve(DBAdminService)
    admin_service.init_database()

    reversed_repo_names = [repo_name for repo_name, _ in REPO_MAPPING][::-1]

    with uow_factory(container) as uow:
        for repo_name in reversed_repo_names:
            repo = getattr(uow, repo_name)
            repo.delete_all()

    cnts = count_entries(test_container)
    for repo_name in reversed_repo_names:
        assert cnts[repo_name] == 0, f"Expected 0 records in {repo_name} repo"
