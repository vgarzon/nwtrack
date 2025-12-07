"""
nwtrack: Net worth tracker app experimental script

Experiment with dependency injection container
"""

from nwtrack.config import Config, load_config
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.repos import NwTrackRepository
from nwtrack.container import Container, Lifetime
from nwtrack.services import NWTrackService


def setup_container() -> Container:
    print(f"Initializing container.")
    container = Container()

    container.register(
        Config,
        lambda c: load_config(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        DBConnectionManager,
        lambda c: SQLiteConnectionManager(c.resolve(Config)),
        lifetime=Lifetime.SINGLETON,
    ).register(
        NwTrackRepository,
        lambda c: NwTrackRepository(c.resolve(DBConnectionManager)),
    ).register(
        NWTrackService,
        lambda c: NWTrackService(c.resolve(Config), c.resolve(NwTrackRepository)),
    )
    return container


def main():
    input_files = {
        "currencies": "data/reference/currencies.csv",
        "account_types": "data/reference/account_types.csv",
        "accounts": "data/sample/accounts.csv",
        "balances": "data/sample/balances.csv",
    }
    as_of_date = "2024-02-01"

    container = setup_container()
    repo = container.resolve(NwTrackRepository)
    svc = container.resolve(NWTrackService)

    svc.init_database()
    svc.initialize_reference_data(
        currencies_path=input_files["currencies"],
        account_types_path=input_files["account_types"],
    )
    svc.insert_sample_data(
        accounts_path=input_files["accounts"],
        balances_path=input_files["balances"],
    )

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
