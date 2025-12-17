"""
nwtrack: Net worth tracker

Example script to demo container, services, and repository usage with balance data
"""

from nwtrack.compose import setup_basic_container
from nwtrack.services import NWTrackService
from nwtrack.admin import AdminService


def main():
    input_files = {
        "currencies": "data/sample/currencies.csv",
        "account_types": "data/sample/account_types.csv",
        "accounts": "data/sample/accounts.csv",
        "balances": "data/sample/balances.csv",
    }
    account_name = "bank_1_checking"
    month = "2024-06"
    new_amount = 530

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

    svc.print_active_accounts()
    svc.print_net_worth_history()

    print("Before update:")
    svc.print_net_worth_on_month(month=month)

    svc.update_balance(
        account_name=account_name,
        month=month,
        new_amount=new_amount,
    )
    print("After update:")
    svc.print_net_worth_on_month(month=month)

    svc.close_repo()


if __name__ == "__main__":
    main()
