"""
Demo unit of work pattern implementation.
"""

from nwtrack.container import Container
from nwtrack.compose import build_uow_container
from nwtrack.admin import AdminService
from nwtrack.services import NWTrackService
from nwtrack.dbmanager import DBConnectionManager


def demo_init(container: Container) -> None:
    input_files = {
        "currencies": "data/sample/currencies.csv",
        "categories": "data/sample/categories.csv",
        "accounts": "data/sample/accounts.csv",
        "balances": "data/sample/balances.csv",
        "exchange_rates": "data/sample/exchange_rates.csv",
    }

    container.resolve(AdminService).init_database()

    svc = container.resolve(NWTrackService)
    svc.initialize_reference_data(
        currencies_path=input_files["currencies"],
        categories_path=input_files["categories"],
    )
    svc.insert_sample_data(
        accounts_path=input_files["accounts"],
        balances_path=input_files["balances"],
    )
    svc.insert_exchange_rates(input_files["exchange_rates"])


def demo_balance(container: Container) -> None:
    account_name = "bank_1_checking"
    month = "2024-06"
    new_amount = 530

    svc = container.resolve(NWTrackService)

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


def demo_exchange_rate(container: Container) -> None:
    month = "2024-06"

    svc = container.resolve(NWTrackService)

    svc.print_exchange_rate("CNY", month)
    svc.print_exchange_rate_history("CHF")
    try:
        svc.print_exchange_rate_history("EUR")
    except ValueError as e:
        print(e)


def demo_roll_forward(container: Container) -> None:
    month = "2025-11"

    svc = container.resolve(NWTrackService)

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
