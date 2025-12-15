"""
nwtrack: Net worth tracker

Experiment with data model, database operations, and services.
"""

from nwtrack.config import Config, load_config
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.repos import NwTrackRepository
from nwtrack.services import NWTrackService
from nwtrack.container import Container, Lifetime


def setup_container() -> Container:
    print("Initializing container.")
    container = Container()

    container.register(
        Config,
        lambda _: load_config(),
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
        "currencies": "data/sample/currencies.csv",
        "account_types": "data/sample/account_types.csv",
        "accounts": "data/sample/accounts.csv",
        "balances": "data/sample/balances.csv",
        "exchange_rates": "data/sample/exchange_rates.csv",
    }
    account_name = "bank_1_checking"
    year = 2024
    month = 6
    new_amount = 530

    container = setup_container()
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

    svc.print_active_accounts()
    svc.print_net_worth_history()

    # update balance for account_id 1 on 2024-02-01 to 530
    print("Before update:")
    svc.print_net_worth_at_year_month(year=year, month=month)

    svc.update_balance(
        account_name=account_name,
        year=year,
        month=month,
        new_amount=new_amount,
    )
    print("After update:")
    svc.print_net_worth_at_year_month(year=year, month=month)

    svc.close_repo()


if __name__ == "__main__":
    main()
