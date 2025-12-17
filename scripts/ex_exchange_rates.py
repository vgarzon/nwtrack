"""
nwtrack: Net worth tracker

Example script demonstrating exchange rage data handling.
"""

from nwtrack.compose import setup_basic_container
from nwtrack.admin import AdminService
from nwtrack.services import NWTrackService


def main():
    input_files = {
        "currencies": "data/sample/currencies.csv",
        "account_types": "data/sample/account_types.csv",
        "exchange_rates": "data/sample/exchange_rates.csv",
    }
    month = "2024-06"

    container = setup_basic_container()
    admin_svc = container.resolve(AdminService)
    svc = container.resolve(NWTrackService)

    admin_svc.init_database()
    svc.initialize_reference_data(
        currencies_path=input_files["currencies"],
        account_types_path=input_files["account_types"],
    )
    svc.insert_exchange_rates(input_files["exchange_rates"])

    svc.print_exchange_rate("CNY", month)
    svc.print_exchange_rate_history("CHF")
    try:
        svc.print_exchange_rate_history("EUR")
    except ValueError as e:
        print(e)

    svc.close_repo()


if __name__ == "__main__":
    main()
