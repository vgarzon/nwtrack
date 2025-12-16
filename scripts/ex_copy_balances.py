"""
nwtrack: Net worth tracker

Example usage: Copy all active balances from one month to the next.
"""

from nwtrack.common import setup_basic_container
from nwtrack.services import NWTrackService


def main():
    input_files = {
        "currencies": "data/sample/currencies.csv",
        "account_types": "data/sample/account_types.csv",
        "accounts": "data/sample/accounts.csv",
        "balances": "data/sample/balances.csv",
    }
    year = 2025
    month = 11

    container = setup_basic_container()
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

    print("Before roll forward:")
    svc.print_balances_at_year_month(year=year, month=month)
    print(f"Copying balances from {year}-{month:02d} to {year}-{month + 1:02d}...")
    svc.copy_balances_to_next_month(year=year, month=month)
    print("After copying:")
    svc.print_balances_at_year_month(year=year, month=month + 1)

    svc.close_repo()


if __name__ == "__main__":
    main()
