"""
Test cases for database connection and unit of work functionalities.
"""

from nwtrack.bootstrap.composition import build_data_services_container

from nwtrack.admin import DBAdminService
from nwtrack.infra.config.settings import Settings
from nwtrack.bootstrap.container import Container
from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.infra.sqlite.db_manager import SQLiteConnectionManager
from tests.data.basic import TEST_DATA

INSERT_QUERIES: dict[str, str] = {
    "currencies": """
        INSERT INTO currencies (code, description)
        VALUES (:code, :description);
        """,
    "categories": """
        INSERT INTO categories (name, side)
        VALUES (:name, :side);
        """,
    "accounts": """
        INSERT INTO accounts (id, name, description, category, currency, status)
        VALUES (:id, :name, :description, :category, :currency, :status);
        """,
    "balances": """
        INSERT INTO balances (account_id, month, amount)
        VALUES (:account_id, :month, :amount);
        """,
    "exchange_rates": """
        INSERT INTO exchange_rates (currency, month, rate)
        VALUES (:currency, :month, :rate);
        """,
}


def get_table_names(db_manager: DBConnectionManager) -> list[str]:
    """Get the names of all tables in the database."""
    cur = db_manager.execute("SELECT name FROM sqlite_master WHERE type='table';")
    rows = cur.fetchall()
    return [row["name"] for row in rows]


def table_exists(db_manager: DBConnectionManager, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cur = db_manager.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (table_name,),
    )
    res = cur.fetchone()
    return res["name"] == table_name if res else False


def table_is_empty(db_manager: DBConnectionManager, table_name: str) -> bool:
    """Check if a table is empty."""
    cur = db_manager.execute(f"SELECT EXISTS (SELECT 1 FROM {table_name}) AS x;")
    res = cur.fetchone()
    return res["x"] == 0 if res else True


def insert_data_with_query(db_manager: DBConnectionManager) -> None:
    """Populate initial data into the database."""
    for table, data in TEST_DATA.items():
        query = INSERT_QUERIES[table]
        rowcnt = db_manager.execute_many(query, data)
        print(f"Inserted {rowcnt} into '{table}'.")


def get_table_count(db_manager: DBConnectionManager, table_name: str) -> int:
    """Count rows in table."""

    cur = db_manager.execute(f"SELECT COUNT(*) AS cnt FROM {table_name};")
    res = cur.fetchone()
    return res["cnt"] if res else 0


def test_db_config(base_container: Container, base_config: Settings) -> None:
    """Test database config."""
    container = build_data_services_container(base_container)
    settings: Settings = container.resolve(Settings)
    assert settings.db_file_path == base_config.db_file_path
    assert settings.db_ddl_path == base_config.db_ddl_path


def test_initialize_database(base_container: Container) -> None:
    """Test database initialization."""
    container = build_data_services_container(base_container)
    admin_service: DBAdminService = container.resolve(DBAdminService)
    db_manager: SQLiteConnectionManager = container.resolve(DBConnectionManager)
    admin_service.init_database()
    row = db_manager.execute("PRAGMA database_list;").fetchone()
    assert row is not None
    assert "file" in row.keys()


def test_tables_exist(base_container: Container) -> None:
    """Test that expected tables exist in the database."""
    container = build_data_services_container(base_container)
    admin_service: DBAdminService = container.resolve(DBAdminService)
    db_manager: SQLiteConnectionManager = container.resolve(DBConnectionManager)
    admin_service.init_database()
    table_names = get_table_names(db_manager)

    assert len(table_names) == 5, "Expected 5 tables in the database."
    assert "balances" in table_names, "Table 'balances' should exist."
    assert "transactions" not in table_names, "Table 'transactions' should not exist"
    assert table_exists(db_manager, "accounts"), "Table 'accounts' should exist."
    assert table_is_empty(db_manager, "balances"), "Table 'balances' should be empty."


def test_insert_data_with_query(base_container: Container) -> None:
    """Test populating initial data into the database."""
    container = build_data_services_container(base_container)
    admin_service: DBAdminService = container.resolve(DBAdminService)
    db_manager: SQLiteConnectionManager = container.resolve(DBConnectionManager)
    admin_service.init_database()
    insert_data_with_query(db_manager)

    assert get_table_count(db_manager, "currencies") == 3, "Expected 3 currencies"
    assert get_table_count(db_manager, "categories") == 3, "Expected 3 categories"
    assert get_table_count(db_manager, "accounts") == 3, "Expected 3 accounts"
    assert get_table_count(db_manager, "balances") == 9, "Expected 9 balances"
    assert get_table_count(db_manager, "exchange_rates") == 6, (
        "Expected 6 exchange rates"
    )
