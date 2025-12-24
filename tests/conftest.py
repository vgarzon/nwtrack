"""
Pytest fixtures and test container setup for nwtrack application.
"""

import pytest
from nwtrack.config import Config
from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.container import Container, Lifetime
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.services import InitDataService, ReportService, UpdateService
from nwtrack.unitofwork import SQLiteUnitOfWork, UnitOfWork
from nwtrack.fileio import csv_to_records
from nwtrack.mappers import MapperRegistry, build_mapper_registry


def get_test_config() -> Config:
    """Test configuration with in-memory database."""
    return Config(
        db_file_path=":memory:",
        db_ddl_path="sql/nwtrack_ddl.sql",
    )


@pytest.fixture(scope="module")
def test_container() -> Container:
    """Setup test container with SQLite Unit of Work.

    Returns:
        Container: Configured DI container.
    """
    container = Container()
    container.register(
        Config,
        lambda _: get_test_config(),
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
        UnitOfWork,
        lambda c: SQLiteUnitOfWork(
            c.resolve(DBConnectionManager), c.resolve(MapperRegistry)
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


@pytest.fixture(scope="module")
def test_file_paths() -> dict[str, str]:
    """Provide file paths for test CSV data.

    Returns:
        dict[str, str]: Mapping of table names to CSV file paths.
    """
    return {
        "currencies": "tests/data/csv/currencies.csv",
        "categories": "tests/data/csv/categories.csv",
        "accounts": "tests/data/csv/accounts.csv",
        "balances": "tests/data/csv/balances.csv",
        "exchange_rates": "tests/data/csv/exchange_rates.csv",
    }


@pytest.fixture(scope="module")
def test_entities(
    test_file_paths: dict[str, str], test_container
) -> dict[str, list[dict[str, str]]]:
    """Load sample data from CSV files for testing.

    Args:
        file_paths (dict[str, str]): Mapping of table names to CSV file paths.

    Returns:
        dict[str, list[dict[str, str]]]: Loaded data for each table.
    """
    print("Loading test data from CSV files...")
    records = {name: csv_to_records(path) for name, path in test_file_paths.items()}

    # NOTE: storing liabilities as positive amounts
    for row in records["balances"]:
        row["amount"] = abs(int(row["amount"]))

    data_svc: InitDataService = test_container.resolve(InitDataService)
    entities = data_svc._records_to_entities(records)

    return entities
