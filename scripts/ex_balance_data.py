"""
nwtrack: Net worth tracker

Example script to demo container, services, and repository usage with balance data
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
    account_name = "bank_1_checking"
    year = 2024
    month = 6
    new_amount = 530

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
