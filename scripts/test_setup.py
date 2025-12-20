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


def test_initialize_database(container: Container) -> None:
    admin_service: DBAdminService = container.resolve(DBAdminService)
    admin_service.init_database()

    cfg: Config = container.resolve(Config)
    assert cfg.db_file_path == ":memory:"
    assert cfg.db_ddl_path == "sql/nwtrack_ddl.sql"

    uow: SQLiteUnitOfWork = container.resolve(UnitOfWork)
    row = uow._db.execute("PRAGMA database_list;").fetchone()
    assert row["file"] == "", "Expected in-memory database."


def main() -> None:
    container = build_test_container()

    test_initialize_database(container)

    pass


if __name__ == "__main__":
    main()
