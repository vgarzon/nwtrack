"""
Pytest fixtures and test container setup for nwtrack application.
"""

import pytest

from nwtrack.application.ports.schema import SchemaManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.bootstrap.composition import build_base_container
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.fileio.csv_io import csv_to_records
from nwtrack.infra.sqlite.sqlalchemy_manager import SQLAlchemySessionManager
from nwtrack.infra.sqlite.sqlalchemy_schema_manager import SQLAlchemySchemaManager


@pytest.fixture(scope="module")
def base_config() -> Settings:
    """Test configuration with in-memory database.

    Uses :memory: for fast test execution with SQLAlchemy.
    """
    return Settings(db_file_path=":memory:")


@pytest.fixture(scope="function")
def base_container(base_config) -> Container:
    """Base container with config and unit of work (SQLAlchemy-based).

    Registered components:
        - Settings
        - SQLAlchemySessionManager
        - SchemaManager
        - UnitOfWork (SQLAlchemy-based)

    Returns:
        Container: Configured DI container with SQLAlchemy ORM
    """
    container = build_base_container()
    container.register(
        Settings,
        lambda _: base_config,
        lifetime=Lifetime.SINGLETON,
    )

    # Register SchemaManager for schema operations
    container.register(
        SchemaManager,
        lambda c: SQLAlchemySchemaManager(
            engine=c.resolve(SQLAlchemySessionManager).engine
        ),
    )

    # Drop and recreate database schema using SchemaManager
    # This ensures each test function starts with a clean database
    schema_manager: SchemaManager = container.resolve(SchemaManager)
    schema_manager.drop_all_tables()
    schema_manager.create_all_tables()

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
