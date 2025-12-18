"""
Demo unit of work pattern implementation.
"""

from nwtrack.container import Container
from nwtrack.compose import build_uow_container
from nwtrack.admin import AdminService
from nwtrack.dbmanager import DBConnectionManager
from nwtrack.services import InitDataService, UpdateService, ReportService
from nwtrack.models import Month


def demo_init(container: Container) -> None:
    input_files = {
        "currencies": "data/sample/currencies.csv",
        "categories": "data/sample/categories.csv",
        "accounts": "data/sample/accounts.csv",
        "balances": "data/sample/balances.csv",
        "exchange_rates": "data/sample/exchange_rates.csv",
    }

    container.resolve(AdminService).init_database()

    data_svc = container.resolve(InitDataService)
    data_svc.initialize_reference_data(
        currencies_path=input_files["currencies"],
        categories_path=input_files["categories"],
    )
    data_svc.insert_sample_data(
        accounts_path=input_files["accounts"],
        balances_path=input_files["balances"],
    )
    data_svc.insert_exchange_rates(input_files["exchange_rates"])


def demo_balance(container: Container) -> None:
    account_name = "bank_1_checking"
    month = "2024-06"
    new_amount = 530

    upd_svc = container.resolve(UpdateService)
    prn_svc = container.resolve(ReportService)

    prn_svc.print_active_accounts()
    prn_svc.print_net_worth_history()

    print("Before update:")
    prn_svc.print_net_worth_on_month(month=month)
    upd_svc.update_balance(
        account_name=account_name,
        month=month,
        new_amount=new_amount,
    )
    print("After update:")
    prn_svc.print_net_worth_on_month(month=month)


def demo_exchange_rate(container: Container) -> None:
    month = "2024-06"

    prn_svc = container.resolve(ReportService)

    prn_svc.print_exchange_rate("CNY", month)
    prn_svc.print_exchange_rate_history("CHF")
    try:
        prn_svc.print_exchange_rate_history("EUR")
    except ValueError as e:
        print(e)


def demo_roll_forward(container: Container) -> None:
    month = "2025-11"

    prn_svc = container.resolve(ReportService)
    upd_svc = container.resolve(UpdateService)

    next_month = str(Month.parse(month).increment())

    print("Before roll forward:")
    prn_svc.print_balances_on_month(month=month)
    print(f"Copying balances from {month} to {next_month}...")
    upd_svc.roll_balances_forward(month=month)
    print("After copying:")
    prn_svc.print_balances_on_month(month=next_month)


def main():
    container = build_uow_container()

    demo_init(container)
    demo_balance(container)
    demo_exchange_rate(container)
    demo_roll_forward(container)

    # DB connection singleton cleanup
    container.resolve(DBConnectionManager).close_connection()


if __name__ == "__main__":
    main()
