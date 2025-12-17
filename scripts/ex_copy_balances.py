"""
nwtrack: Net worth tracker

Example usage: Copy all active balances from one month to the next.
"""

from nwtrack.compose import setup_basic_container
from nwtrack.admin import AdminService
from nwtrack.services import NWTrackService


def main():
    input_files = {
        "currencies": "data/sample/currencies.csv",
        "account_types": "data/sample/account_types.csv",
        "accounts": "data/sample/accounts.csv",
        "balances": "data/sample/balances.csv",
    }
    month = "2025-11"

    container = setup_basic_container()
    admin_svc = container.resolve(AdminService)
    svc = container.resolve(NWTrackService)

    admin_svc.init_database()
    svc.initialize_reference_data(
        currencies_path=input_files["currencies"],
        account_types_path=input_files["account_types"],
    )
    svc.insert_sample_data(
        accounts_path=input_files["accounts"],
        balances_path=input_files["balances"],
    )

    year_int, month_int = map(int, month.split("-"))
    next_month = (
        f"{year_int + 1}-01" if month_int == 12 else f"{year_int}-{month_int + 1:02d}"
    )
    print("Before roll forward:")
    svc.print_balances_on_month(month=month)
    print(f"Copying balances from {month} to {next_month}...")
    svc.copy_balances_to_next_month(month=month)
    print("After copying:")
    svc.print_balances_on_month(month=next_month)

    svc.close_repo()


if __name__ == "__main__":
    main()
