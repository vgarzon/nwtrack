"""
Initialize database and insert seed data from CSV files.
"""

from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.compose import build_base_sqlite_uow_container
from nwtrack.config import Config
from nwtrack.dbmanager import DBConnectionManager
from nwtrack.services import InitDataService
from nwtrack.unitofwork import UnitOfWork
from nwtrack.use_cases.db_initializer import DBInitializerCSV


def main(file_paths: dict[str, str]) -> None:
    container = build_base_sqlite_uow_container()
    container.register(
        DBAdminService,
        lambda c: SQLiteAdminService(c.resolve(Config), c.resolve(DBConnectionManager)),
    ).register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        DBInitializerCSV,
        lambda c: DBInitializerCSV(
            c.resolve(Config), c.resolve(DBAdminService), c.resolve(InitDataService)
        ),
    )

    db_initializer: DBInitializerCSV = container.resolve(DBInitializerCSV)
    db_initializer.run(file_paths)


if __name__ == "__main__":
    file_paths = {
        "currencies": "tests/data/csv/currencies.csv",
        "categories": "tests/data/csv/categories.csv",
        "accounts": "tests/data/csv/accounts.csv",
        "balances": "tests/data/csv/balances.csv",
        "exchange_rates": "tests/data/csv/exchange_rates.csv",
    }
    main(file_paths)
