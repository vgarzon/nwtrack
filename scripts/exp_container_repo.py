"""
nwtrack: Net worth tracker app experimental script

Experiment with dependency injection container
"""

from nwtrack.config import settings
from nwtrack.fileio import csv_file_to_list_dict
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.repos import NwTrackRepository
from nwtrack.container import Container, Lifetime


def setup_container(db_path: str) -> Container:
    print(f"Initializing container with {db_path=}.")
    container = Container()

    container.register(
        DBConnectionManager,
        lambda c: SQLiteConnectionManager(db_path),
        lifetime=Lifetime.SINGLETON,
    ).register(
        NwTrackRepository,
        lambda c: NwTrackRepository(c.resolve(DBConnectionManager)),
        lifetime=Lifetime.SINGLETON,
    )
    return container


def main():
    ddl_script = "sql/nwtrack_ddl.sql"
    currencies_file = "data/reference/currencies.csv"
    account_types_file = "data/reference/account_types.csv"
    accounts_file = "data/sample/accounts.csv"
    balances_file = "data/sample/balances.csv"
    as_of_date = "2024-02-01"

    container = setup_container(settings.db_file_path)

    repo = container.resolve(NwTrackRepository)

    print(f"DDL script: {ddl_script}.")
    repo.init_database(ddl_script)

    print(f"Initializing currency table from {currencies_file}.")
    currencies_data = csv_file_to_list_dict(currencies_file)
    repo.init_currencies(currencies_data)

    print(f"Initializing account types table from {account_types_file}.")
    account_types_data = csv_file_to_list_dict(account_types_file)
    repo.init_account_types(account_types_data)

    accounts_data = csv_file_to_list_dict(accounts_file)
    print(f"Loaded {len(accounts_data)} accounts from {accounts_file}.")
    repo.insert_accounts(accounts_data)

    balances_data = csv_file_to_list_dict(balances_file)
    print(f"Loaded {len(balances_data)} balance records from {balances_file}.")
    repo.insert_balances(balances_data)

    accounts = repo.find_active_accounts()
    for account in accounts:
        print(f"Account ID: {account['id']}, Name: {account['name']}")

    rows = repo.get_net_worth_history()
    for res in rows:
        print(
            f"Date: {res['date']}, assets: {res['total_assets']}, "
            f"liabilities: {res['total_liabilities']}, "
            f"net worth: {res['net_worth']}"
        )

    # update balance for account_id 1 on 2024-02-01 to 530
    print("Before update:")
    repo.print_net_worth_at_date(as_of_date=as_of_date)
    repo.update_account_balance(account_id=1, date=as_of_date, new_amount=530)
    print("After update:")
    repo.print_net_worth_at_date(as_of_date=as_of_date)

    repo.close_db_connection()


if __name__ == "__main__":
    main()
