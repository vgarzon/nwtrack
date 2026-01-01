"""
Pytest fixtures and test container setup for nwtrack application.
"""

from typing import Any
from unittest.mock import Mock

import pytest

from nwtrack.compose import build_sqlite_uow_container
from nwtrack.config import Config
from nwtrack.container import Container, Lifetime
from nwtrack.dbmanager import DBConnectionManager
from nwtrack.fileio import csv_to_records
from nwtrack.mapper_registry import MapperRegistry
from nwtrack.services import InitDataService
from tests.fakes import FakeEntityA, FakeEntityB


@pytest.fixture(scope="module")
def test_config() -> Config:
    """Test configuration with in-memory database."""
    return Config(
        db_file_path=":memory:",
        db_ddl_path="sql/nwtrack_ddl.sql",
    )


@pytest.fixture(scope="module")
def test_container(test_config) -> Container:
    """Setup test container with SQLite Unit of Work and test config.

    Returns:
        Container: Configured DI container.
    """
    container = build_sqlite_uow_container()
    container.register(
        Config,
        lambda _: test_config,
        lifetime=Lifetime.SINGLETON,
    )
    return container


@pytest.fixture(scope="module")
def test_file_paths() -> dict[str, str]:
    """Provide file paths for test CSV data.

    Returns:
        dict[str, str]: Mapping of table names to CSV file paths.
    """
    # NOTE: The order of keys may matters for foreign key constraints
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


@pytest.fixture(scope="function")
def test_db_manager() -> Mock:
    return Mock(spec=DBConnectionManager)


@pytest.fixture(scope="function")
def test_mapper_registry() -> MapperRegistry:
    class MapperA:
        def to_entity(self, data: dict[str, Any]) -> FakeEntityA:
            return FakeEntityA()

        def to_record(self, entity: FakeEntityA) -> dict[str, Any]:
            return {}

    class MapperB:
        def to_entity(self, data: dict[str, Any]) -> FakeEntityB:
            return FakeEntityB()

        def to_record(self, entity: FakeEntityB) -> dict[str, Any]:
            return {}

    mapper_registry = MapperRegistry()
    mapper_registry.register(FakeEntityA, MapperA())
    mapper_registry.register(FakeEntityB, MapperB())

    return mapper_registry
