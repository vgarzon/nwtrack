"""
Initialize database and insert seed data from CSV files.
"""

from nwtrack.compose import build_sqlite_uow_container
from nwtrack.use_cases import DBInitializerCSV


def main() -> None:
    file_paths = {
        "currencies": "tests/data/csv/currencies.csv",
        "categories": "tests/data/csv/categories.csv",
        "accounts": "tests/data/csv/accounts.csv",
        "balances": "tests/data/csv/balances.csv",
        "exchange_rates": "tests/data/csv/exchange_rates.csv",
    }
    container = build_sqlite_uow_container()
    db_initializer = DBInitializerCSV(container)
    db_initializer.run(file_paths)


if __name__ == "__main__":
    main()
