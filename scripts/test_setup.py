"""
Setup database for testing purposes.
"""

from nwtrack.config import Config
from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.container import Container, Lifetime
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.services import InitDataService  # , ReportService, UpdateService
from nwtrack.unitofwork import SQLiteUnitOfWork, UnitOfWork


TEST_DATA: dict[str, list[dict]] = {
    "currencies": [
        {"code": "USD", "description": "United States Dollar"},
        {"code": "CNY", "description": "Chinese Yuan"},
        {"code": "CHF", "description": "Swiss Franc"},
    ],
    "categories": [
        {"name": "checking", "side": "asset"},
        {"name": "savings", "side": "asset"},
        {"name": "mortgage", "side": "liability"},
    ],
    "accounts": [
        {
            "id": 1,
            "name": "checking_1",
            "description": "checking account",
            "category": "checking",
            "currency": "USD",
            "status": "active",
        },
        {
            "id": 2,
            "name": "savings_2",
            "description": "savings account",
            "category": "savings",
            "currency": "USD",
            "status": "active",
        },
        {
            "id": 3,
            "name": "mortgage_3",
            "description": "primary home morgage",
            "category": "mortgage",
            "currency": "USD",
            "status": "active",
        },
    ],
    "balances": [
        {"account_id": 1, "month": "2024-01", "amount": 500},
        {"account_id": 1, "month": "2024-02", "amount": 520},
        {"account_id": 1, "month": "2024-03", "amount": 480},
        {"account_id": 2, "month": "2024-01", "amount": 1500},
        {"account_id": 2, "month": "2024-02", "amount": 1550},
        {"account_id": 2, "month": "2024-03", "amount": 1600},
        {"account_id": 3, "month": "2024-01", "amount": 2500},
        {"account_id": 3, "month": "2024-02", "amount": 2400},
        {"account_id": 3, "month": "2024-03", "amount": 2300},
    ],
    "exchange_rates": [
        {"currency": "CNY", "month": "2024-01", "rate": 0.71},
        {"currency": "CNY", "month": "2024-02", "rate": 0.72},
        {"currency": "CNY", "month": "2024-03", "rate": 0.73},
        {"currency": "CHF", "month": "2024-01", "rate": 1.10},
        {"currency": "CHF", "month": "2024-02", "rate": 1.11},
        {"currency": "CHF", "month": "2024-03", "rate": 1.09},
    ],
}

RAW_QUERIES: dict[str, str] = {
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
        # .register(
        #     UpdateService,
        #     lambda c: UpdateService(uow=lambda: c.resolve(UnitOfWork)),
        # )
        # .register(
        #     ReportService,
        #     lambda c: ReportService(uow=lambda: c.resolve(UnitOfWork)),
        # )
    )


def get_table_names(db: DBConnectionManager) -> list[str]:
    """Get the names of all tables in the database."""
    cur = db.execute("SELECT name FROM sqlite_master WHERE type='table';")
    rows = cur.fetchall()
    return [row["name"] for row in rows]


def table_exists(db: DBConnectionManager, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cur = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (table_name,),
    )
    res = cur.fetchone()
    return res["name"] == table_name if res else False


def table_is_empty(db: DBConnectionManager, table_name: str) -> bool:
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


def populate_initial_data(db: DBConnectionManager) -> None:
    """Populate initial data into the database."""
    for table, data in TEST_DATA.items():
        query = RAW_QUERIES[table]
        rowcnt = db.execute_many(query, data)
        db.commit()
        print(f"Inserted {rowcnt} into '{table}'.")
        cur = db.execute(f"SELECT * FROM {table} LIMIT 2;")
        res = cur.fetchall()
        for row in res:
            print(dict(row))


def hydrate_test_data(container) -> None:
    """Hydrate initial data using InitDataService."""
    init_svc: InitDataService = container.resolve(InitDataService)

    currencies = init_svc.hydrate_currency_records(TEST_DATA["currencies"])
    categories = init_svc.hydrate_category_data(TEST_DATA["categories"])
    accounts = init_svc.hydrate_account_records(TEST_DATA["accounts"])
    balances = init_svc.hydrate_balance_records(TEST_DATA["balances"])
    exchange_rates = init_svc.hydrate_exchange_rate_records(TEST_DATA["exchange_rates"])

    print(currencies)
    print(categories)
    print(accounts)
    print(balances)
    print(exchange_rates)


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
    hydrate_test_data(container)


if __name__ == "__main__":
    main()
