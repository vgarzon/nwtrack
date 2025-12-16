"""
nwtrack: Net worth tracker

Example script demonstrating exchange rage data handling.
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
        "exchange_rates": "data/sample/exchange_rates.csv",
    }
    year, month = 2024, 6

    container = setup_container()
    svc = container.resolve(NWTrackService)

    svc.init_database()
    svc.initialize_reference_data(
        currencies_path=input_files["currencies"],
        account_types_path=input_files["account_types"],
    )
    svc.insert_exchange_rates(input_files["exchange_rates"])

    svc.print_exchange_rate("CNY", year, month)
    svc.print_exchange_rate_history("CHF")
    try:
        svc.print_exchange_rate_history("EUR")
    except ValueError as e:
        print(e)

    svc.close_repo()


if __name__ == "__main__":
    main()
