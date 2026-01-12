"""
Pytest fixtures and test container setup for nwtrack application.
"""

from unittest.mock import Mock

import pytest

from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.fileio.csv_io import csv_to_records


@pytest.fixture(scope="module")
def base_config() -> Settings:
    """Test configuration with in-memory database."""
    return Settings(
        db_file_path=":memory:",
        db_ddl_path="sql/nwtrack_ddl.sql",
    )


@pytest.fixture(scope="function")
def base_container(base_config) -> Container:
    """Base container with config, repo registry, and unit of work.

    Registered components:
        - Settings
        - DBConnectionManager
        - MapperRegistry
        - RepositoryRegistry
        - UnitOfWork,

    Returns:
        Container: Configured DI container.
    """
    container = build_base_sqlite_uow_container()
    container.register(
        Settings,
        lambda _: base_config,
        lifetime=Lifetime.SINGLETON,
    )
    return container


@pytest.fixture(scope="module")
def sample_data_file_paths() -> dict[str, str]:
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


@pytest.fixture(scope="function")
def sample_entities(
    sample_data_file_paths: dict[str, str], base_container
) -> dict[str, list[dict[str, str]]]:
    """Load sample data from CSV files for testing.

    Args:
        file_paths (dict[str, str]): Mapping of table names to CSV file paths.

    Returns:
        dict[str, list[dict[str, str]]]: Loaded data for each table.
    """
    records = {
        name: csv_to_records(path) for name, path in sample_data_file_paths.items()
    }

    # NOTE: storing liabilities as positive amounts
    for row in records["balances"]:
        row["amount"] = abs(int(row["amount"]))

    base_container.register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    )
    data_svc: InitDataService = base_container.resolve(InitDataService)
    entities = data_svc._records_to_entities(records)

    return entities


@pytest.fixture(scope="module")
def mock_db_manager() -> Mock:
    return Mock(spec=DBConnectionManager)
