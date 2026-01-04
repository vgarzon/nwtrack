"""
Test initial data service
"""

import pytest

from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.config import Config
from nwtrack.container import Container
from nwtrack.dbmanager import DBConnectionManager
from nwtrack.services import InitDataService
from nwtrack.unitofwork import UnitOfWork
from tests.helpers import (
    count_entries,
    init_db_tables_from_csv,
    init_db_tables_w_entities,
)


@pytest.fixture
def configured_container(base_container: Container) -> None:
    """Configure container for tests."""
    return base_container.register(
        DBAdminService,
        lambda c: SQLiteAdminService(c.resolve(Config), c.resolve(DBConnectionManager)),
    ).register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    )


def test_init_data_from_csv(
    configured_container: Container, sample_data_file_paths: dict[str, str]
) -> None:
    """Test initializing database and loading sample data from CSV files"""
    init_db_tables_from_csv(configured_container, sample_data_file_paths)
    cnts = count_entries(configured_container)
    assert cnts["currencies"] == 3, "Expected 3 currencies"
    assert cnts["categories"] == 4, "Expected 4 categories"
    assert cnts["accounts"] == 4, "Expected 4 accounts"
    assert cnts["balances"] == 42, "Expected 42 balances"
    assert cnts["exchange_rates"] == 48, "Expected 48 exchange rates"


def test_init_data_entities(
    configured_container: Container, sample_entities: dict[str, list]
) -> None:
    """Test initializing database and loading sample data."""
    init_db_tables_w_entities(configured_container, sample_entities)
    cnts = count_entries(configured_container)
    assert cnts["currencies"] == 3, "Expected 3 currencies"
    assert cnts["categories"] == 4, "Expected 4 categories"
    assert cnts["accounts"] == 4, "Expected 4 accounts"
    assert cnts["balances"] == 42, "Expected 42 balances"
    assert cnts["exchange_rates"] == 48, "Expected 48 exchange rates"
