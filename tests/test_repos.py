"""
Test cases for repository management functionalities.
"""

from nwtrack.container import Container
from nwtrack.unitofwork import UnitOfWork
from nwtrack.admin import DBAdminService
from nwtrack.services import ReportService
from tests.data.basic import TEST_DATA


# repo label, table name
REPO_MAPPING = [
    ("currencies", "currencies"),
    ("categories", "categories"),
    ("accounts", "accounts"),
    ("balances", "balances"),
    ("exchange_rates", "exchange_rates"),
]


def count_records(test_container: Container) -> dict[str, int]:
    """Count records from all repos."""

    prn_svc: ReportService = test_container.resolve(ReportService)

    return prn_svc.count_records()


def uow_factory(test_container: Container) -> UnitOfWork:
    return test_container.resolve(UnitOfWork)


def test_insert_hydrated(test_container) -> None:
    """Test inserting hydrated objects."""

    admin_service: DBAdminService = test_container.resolve(DBAdminService)
    admin_service.init_database()

    with uow_factory(test_container) as uow:
        for repo_name, table_name in REPO_MAPPING:
            repo = getattr(uow, repo_name)
            entities = repo.hydrate_many(TEST_DATA[table_name])
            repo.insert_many(entities)

    cnts = count_records(test_container)
    assert cnts["currencies"] == 3, "Expected 3 currencies"
    assert cnts["categories"] == 3, "Expected 3 categories"
    assert cnts["accounts"] == 3, "Expected 3 accounts"
    assert cnts["balances"] == 9, "Expected 9 balances"
    assert cnts["exchange_rates"] == 6, "Expected 6 exchange rates"


def test_delete_records(test_container: Container) -> None:
    """Delete all records from all tables."""

    admin_service: DBAdminService = test_container.resolve(DBAdminService)
    admin_service.init_database()

    reversed_repo_names = [repo_name for repo_name, _ in REPO_MAPPING][::-1]

    with uow_factory(test_container) as uow:
        for repo_name in reversed_repo_names:
            repo = getattr(uow, repo_name)
            repo.delete_all()

    cnts = count_records(test_container)
    for repo_name in reversed_repo_names:
        assert cnts[repo_name] == 0, f"Expected 0 records in {repo_name} repo"
