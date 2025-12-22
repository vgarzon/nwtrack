"""
Test cases for database connection and unit of work functionalities.
"""

from nwtrack.config import Config
from nwtrack.container import Container
from nwtrack.admin import DBAdminService
from nwtrack.unitofwork import UnitOfWork
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


def uow_factory(test_container: Container) -> UnitOfWork:
    return test_container.resolve(UnitOfWork)


def get_table_names(uow: UnitOfWork) -> list[str]:
    """Get the names of all tables in the database."""
    cur = uow._db.execute("SELECT name FROM sqlite_master WHERE type='table';")  # type: ignore[attr-defined]
    rows = cur.fetchall()
    return [row["name"] for row in rows]


def table_exists(uow: UnitOfWork, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cur = uow._db.execute(  # type: ignore[attr-defined]
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (table_name,),
    )
    res = cur.fetchone()
    return res["name"] == table_name if res else False


def table_is_empty(uow: UnitOfWork, table_name: str) -> bool:
    """Check if a table is empty."""
    cur = uow._db.execute(f"SELECT EXISTS (SELECT 1 FROM {table_name}) AS x;")  # type: ignore[attr-defined]
    res = cur.fetchone()
    return res["x"] == 0 if res else True


def insert_data_with_query(uow: UnitOfWork) -> None:
    """Populate initial data into the database."""
    for table, data in TEST_DATA.items():
        query = INSERT_QUERIES[table]
        rowcnt = uow._db.execute_many(query, data)  # type: ignore[attr-defined]
        print(f"Inserted {rowcnt} into '{table}'.")


def get_table_count(uow: UnitOfWork, table_name: str) -> int:
    """Count rows in table."""

    cur = uow._db.execute(f"SELECT COUNT(*) AS cnt FROM {table_name};")  # type: ignore[attr-defined]
    res = cur.fetchone()
    return res["cnt"] if res else 0


def test_initialize_database(test_container: Container) -> None:
    """Test database initialization."""
    admin_service: DBAdminService = test_container.resolve(DBAdminService)
    admin_service.init_database()

    cfg: Config = test_container.resolve(Config)
    assert cfg.db_file_path == ":memory:"
    assert cfg.db_ddl_path == "sql/nwtrack_ddl.sql"

    with uow_factory(test_container) as uow:
        row = uow._db.execute("PRAGMA database_list;").fetchone()  # type: ignore[attr-defined]

    assert row["file"] == "", "Expected in-memory database."


def test_tables_exist(test_container: Container) -> None:
    """Test that expected tables exist in the database."""

    admin_service: DBAdminService = test_container.resolve(DBAdminService)
    admin_service.init_database()

    with uow_factory(test_container) as uow:
        table_names = get_table_names(uow)

    assert len(table_names) == 5, "Expected 5 tables in the database."
    assert "balances" in table_names, "Table 'balances' should exist."
    assert "transactions" not in table_names, "Table 'transactions' should not exist"

    with uow_factory(test_container) as uow:
        assert table_exists(uow, "accounts"), "Table 'accounts' should exist."
        assert table_is_empty(uow, "balances"), "Table 'balances' should be empty."


def test_insert_data_with_query(test_container: Container) -> None:
    """Test populating initial data into the database."""

    admin_service: DBAdminService = test_container.resolve(DBAdminService)
    admin_service.init_database()

    with uow_factory(test_container) as uow:
        insert_data_with_query(uow)

    with uow_factory(test_container) as uow:
        assert get_table_count(uow, "currencies") == 3, "Expected 3 currencies"
        assert get_table_count(uow, "categories") == 3, "Expected 3 categories"
        assert get_table_count(uow, "accounts") == 3, "Expected 3 accounts"
        assert get_table_count(uow, "balances") == 9, "Expected 9 balances"
        assert get_table_count(uow, "exchange_rates") == 6, "Expected 6 exchange rates"
