"""
Setup database for testing purposes.
"""

from nwtrack.config import Config
from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.container import Container, Lifetime
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.services import InitDataService, ReportService, UpdateService
from nwtrack.unitofwork import SQLiteUnitOfWork, UnitOfWork


def test_config() -> Config:
    """Test configuration with in-memory database."""
    return Config(
        db_file_path=":memory:",
        db_ddl_path="sql/nwtrack_ddl.sql",
    )


def build_test_container() -> Container:
    """Setup test container with SQLite Unit of Work.

    Returns:
        Container: Configured DI container.
    """
    return (
        Container()
        .register(
            Config,
            lambda _: test_config(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            DBConnectionManager,
            lambda c: SQLiteConnectionManager(c.resolve(Config)),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            UnitOfWork,
            lambda c: SQLiteUnitOfWork(c.resolve(DBConnectionManager)),
        )
        .register(
            DBAdminService,
            lambda c: SQLiteAdminService(
                c.resolve(Config), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            UpdateService,
            lambda c: UpdateService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            ReportService,
            lambda c: ReportService(uow=lambda: c.resolve(UnitOfWork)),
        )
    )


def get_table_names(db: SQLiteConnectionManager) -> list[str]:
    """Get the names of all tables in the database."""
    cur = db.execute("SELECT name FROM sqlite_master WHERE type='table';")
    rows = cur.fetchall()
    return [row["name"] for row in rows]


def table_exists(db: SQLiteConnectionManager, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cur = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (table_name,),
    )
    res = cur.fetchone()
    return res["name"] == table_name if res else False


def table_is_empty(db: SQLiteConnectionManager, table_name: str) -> bool:
    """Check if a table is empty."""
    cur = db.execute(f"SELECT EXISTS (SELECT 1 FROM {table_name}) AS x;")
    res = cur.fetchone()
    return res["x"] == 0 if res else True


def test_initialize_database(container: Container) -> None:
    """Test database initialization."""
    admin_service: DBAdminService = container.resolve(DBAdminService)
    admin_service.init_database()

    cfg: Config = container.resolve(Config)
    assert cfg.db_file_path == ":memory:"
    assert cfg.db_ddl_path == "sql/nwtrack_ddl.sql"


def test_tables_exist(container: Container) -> None:
    """Test that expected tables exist in the database."""
    uow: SQLiteUnitOfWork = container.resolve(UnitOfWork)

    row = uow._db.execute("PRAGMA database_list;").fetchone()
    assert row["file"] == "", "Expected in-memory database."

    table_names = get_table_names(uow._db)
    assert len(table_names) == 6, "Expected 6 tables in the database."

    assert table_exists(uow._db, "accounts"), "Table 'accounts' should exist."
    assert "balances" in table_names, "Table 'balances' should exist."
    assert "transactions" not in table_names, "Table 'transactions' should not exist"
    assert table_is_empty(uow._db, "balances"), "Table 'balances' should be empty."


TABLE_DATA = {
    "currencies": (
        """
        INSERT INTO currencies (code, description)
        VALUES (?, ?);
        """,
        [
            ("USD", "United States Dollar"),
            ("CNY", "Chinese Yuan"),
            ("CHF", "Swiss Franc"),
        ],
    ),
    "categories": (
        """
        INSERT INTO categories (name, side)
        VALUES (?, ?);
        """,
        [
            ("checking", "asset"),
            ("savings", "asset"),
            ("mortgage", "liability"),
        ],
    ),
    "accounts": (
        """
        INSERT INTO accounts (id, name, description, category, currency, status)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        [
            (1, "checking_1", "checking account", "checking", "USD", "active"),
            (2, "savings_2", "savings account", "savings", "USD", "active"),
            (3, "mortgage_3", "primary home morgage", "mortgage", "USD", "active"),
        ],
    ),
    "balances": (
        """
        INSERT INTO balances (account_id, month, amount)
        VALUES (?, ?, ?);
        """,
        [
            (1, "2024-01", 500),
            (1, "2024-02", 520),
            (1, "2024-03", 480),
            (2, "2024-01", 1500),
            (2, "2024-02", 1550),
            (2, "2024-03", 1600),
            (3, "2024-01", 2500),
            (3, "2024-02", 2400),
            (3, "2024-03", 2300),
        ],
    ),
    "exchange_rates": (
        """
        INSERT INTO exchange_rates (currency, month, rate)
        VALUES (?, ?, ?);
        """,
        [
            ("CNY", "2024-01", 0.71),
            ("CNY", "2024-02", 0.72),
            ("CNY", "2024-03", 0.73),
            ("CHF", "2024-01", 1.10),
            ("CHF", "2024-02", 1.11),
            ("CHF", "2024-03", 1.09),
        ],
    ),
}


def populate_initial_data(db: SQLiteConnectionManager) -> None:
    """Populate initial data into the database."""
    for table, (query, data) in TABLE_DATA.items():
        rowcnt = db.execute_many(query, data)
        db.commit()
        print(f"Inserted {rowcnt} into '{table}'.")
        cur = db.execute(f"SELECT * FROM {table} LIMIT 2;")
        res = cur.fetchall()
        for row in res:
            print(dict(row))


def test_populate_initial_data(container: Container) -> None:
    """Test populating initial data into the database."""
    uow: SQLiteUnitOfWork = container.resolve(UnitOfWork)

    populate_initial_data(uow._db)

    # assert not table_is_empty(uow._db, "accounts"), (
    #     "Table 'accounts' should not be empty after initialization."
    # )


def main() -> None:
    container = build_test_container()
    test_initialize_database(container)
    test_tables_exist(container)
    test_populate_initial_data(container)


if __name__ == "__main__":
    main()
