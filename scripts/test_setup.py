"""
Setup database for testing purposes.
"""

from nwtrack.config import Config
from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.container import Container, Lifetime
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.services import InitDataService, ReportService  # , UpdateService
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


# repo label, table name
REPO_MAPPING = [
    ("currency", "currencies"),
    ("category", "categories"),
    ("account", "accounts"),
    ("balance", "balances"),
    ("exchange_rate", "exchange_rates"),
]


def get_test_config() -> Config:
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
            lambda _: get_test_config(),
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
        .register(
            ReportService,
            lambda c: ReportService(uow=lambda: c.resolve(UnitOfWork)),
        )
    )


def uow_factory(container: Container) -> SQLiteUnitOfWork:
    return container.resolve(UnitOfWork)


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


def insert_data_with_query(db: DBConnectionManager) -> None:
    """Populate initial data into the database."""
    for table, data in TEST_DATA.items():
        query = INSERT_QUERIES[table]
        rowcnt = db.execute_many(query, data)
        db.commit()
        print(f"Inserted {rowcnt} into '{table}'.")


def count_records(container: Container) -> dict[str, int]:
    """Count records from all repos."""

    prn_svc: ReportService = container.resolve(ReportService)

    return prn_svc.count_records()


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
    assert len(table_names) == 5, "Expected 5 tables in the database."

    assert table_exists(uow._db, "accounts"), "Table 'accounts' should exist."
    assert "balances" in table_names, "Table 'balances' should exist."
    assert "transactions" not in table_names, "Table 'transactions' should not exist"
    assert table_is_empty(uow._db, "balances"), "Table 'balances' should be empty."


def test_insert_data_with_query(container: Container) -> None:
    """Test populating initial data into the database."""
    uow: SQLiteUnitOfWork = container.resolve(UnitOfWork)

    insert_data_with_query(uow._db)

    cnts = count_records(container)
    assert cnts["currency"] == 3, "Expected 3 currencies"
    assert cnts["category"] == 3, "Expected 3 categories"
    assert cnts["account"] == 3, "Expected 3 accounts"
    assert cnts["balance"] == 9, "Expected 9 balances"
    assert cnts["exchange_rate"] == 6, "Expected 6 exchange rates"


def test_delete_records(container: Container) -> None:
    """Delete all records from all tables."""

    reversed_repo_names = [repo_name for repo_name, _ in REPO_MAPPING][::-1]

    with uow_factory(container) as uow:
        for repo_name in reversed_repo_names:
            repo = getattr(uow, repo_name)
            repo.delete_all()

    cnts = count_records(container)
    for repo_name in reversed_repo_names:
        assert cnts[repo_name] == 0, f"Expected 0 records in {repo_name} repo"


def test_insert_hydrated(container) -> None:
    """Test inserting hydrated objects."""

    with uow_factory(container) as uow:
        for repo_name, table_name in REPO_MAPPING:
            print(repo_name, table_name)
            repo = getattr(uow, repo_name)
            entities = repo.hydrate_many(TEST_DATA[table_name])
            repo.insert_many(entities)

    cnts = count_records(container)
    for repo_name, _ in REPO_MAPPING:
        print(f"{repo_name}: {cnts[repo_name]}")


def main() -> None:
    container = build_test_container()
    test_initialize_database(container)
    test_tables_exist(container)
    test_insert_data_with_query(container)
    test_delete_records(container)
    test_insert_hydrated(container)


if __name__ == "__main__":
    main()
