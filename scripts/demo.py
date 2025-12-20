"""
Demo unit of work pattern implementation.
"""

from nwtrack.container import Container
from nwtrack.compose import build_sqlite_uow_container
from nwtrack.admin import DBAdminService
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
    print("*** Demo initializing database and loading sample data ***")

    container.resolve(DBAdminService).init_database()

    data_svc: InitDataService = container.resolve(InitDataService)
    data_svc.initialize_reference_data(
        currencies_path=input_files["currencies"],
        categories_path=input_files["categories"],
    )
    data_svc.insert_sample_data(
        accounts_path=input_files["accounts"],
        balances_path=input_files["balances"],
    )
    data_svc.insert_exchange_rates(input_files["exchange_rates"])


def demo_accounts(container: Container) -> None:
    print("*** Demo retrieving accounts ***")

    prn_svc: ReportService = container.resolve(ReportService)

    active_accounts = prn_svc.get_accounts(active_only=True)
    assert len(active_accounts) == 8, "Expecting 8 active accounts"
    assert active_accounts[-1].id == 8, "Expecting last active account ID == 8"
    assert active_accounts[-1].name == "credit_cards_1"

    all_accounts = prn_svc.get_accounts(active_only=False)
    assert len(all_accounts) == 10, "Expecting 10 total accounts"
    assert all_accounts[-1].id == 10, "Expecting last account ID == 10"
    assert all_accounts[-1].name == "mortgage_1"


def demo_net_worth(container: Container) -> None:
    month_str = "2025-11"

    print("*** Demo retrieving net worth ***")

    month = Month.parse(month_str)
    prn_svc: ReportService = container.resolve(ReportService)

    net_worth = prn_svc.get_net_worth(month=month)
    assert net_worth.month == month, "Net worth month mismatch"
    assert net_worth.assets == 277000, "Net worth assets mismatch"
    assert net_worth.liabilities == 600, "Net worth liabilities mismatch"
    assert net_worth.net_worth == 276400, "Net worth total mismatch"

    prn_svc.print_net_worth(month=month)

    net_worth_hist = prn_svc.get_net_worth_history()
    assert len(net_worth_hist) == 51, "Net worth history length mismatch"
    assert net_worth_hist[-1].month == Month(2025, 11), (
        "Net worth history last month mismatch"
    )
    assert net_worth_hist[-1].net_worth == 276400, (
        "Net worth history last total mismatch"
    )


def demo_fetch_balance(container: Container) -> None:
    account_name = "bank_1_checking"
    month_str = "2025-10"

    print("*** Demo fetching balance data ***")

    prn_svc: ReportService = container.resolve(ReportService)
    month = Month.parse(month_str)

    account_map = {acc.id: acc for acc in prn_svc.get_accounts()}
    single_bal = prn_svc.get_balance(month, account_name)

    assert single_bal.id == 401, "Balance id mismatch"
    assert account_map[single_bal.account_id].name == account_name, (
        "Balance account name mismatch"
    )
    assert single_bal.account_id == 2, "Balance account id mismatch"
    assert single_bal.month == month, "Balance month mismatch"
    assert single_bal.amount == 200, "Balance amount mismatch"

    month_bals = prn_svc.get_month_balances(month)
    assert len(month_bals) == 8, "Month balances length mismatch"

    for acc in prn_svc.get_balances_sample():
        print(acc)


def demo_update_balance(container: Container) -> None:
    account_name = "bank_1_checking"
    month_str = "2024-06"
    new_amount = 500

    print("*** Demo updating existing balance ***")

    month = Month.parse(month_str)
    upd_svc: UpdateService = container.resolve(UpdateService)
    prn_svc: ReportService = container.resolve(ReportService)

    print("Before update:")
    prn_svc.print_balance(month, account_name)
    before = prn_svc.get_balance(month, account_name)
    assert before.amount == 300, "Pre-update balance amount mismatch"
    upd_svc.update_balance(
        account_name=account_name,
        month=month,
        new_amount=new_amount,
    )
    after = prn_svc.get_balance(month, account_name)
    assert after.amount == new_amount, "Post-update balance amount mismatch"
    print("After update:")
    prn_svc.print_balance(month, account_name)
    prn_svc.print_month_balances(month)


def demo_exchange_rate(container: Container) -> None:
    print("*** Demo retrieving exchange rates ***")

    currency_codes = ["CNY", "EUR"]
    month_str = "2015-12"

    prn_svc: ReportService = container.resolve(ReportService)
    month = Month.parse(month_str)

    rate = prn_svc.get_exchange_rate(month, currency_codes[0])
    assert rate is not None, "Exchange rate not found"
    assert rate.rate == 6.5, "Exchange rate value mismatch"
    prn_svc.print_exchange_rate(month, currency_codes[0])

    rates = prn_svc.get_month_exchange_rates(month)
    assert len(rates) == 2, "Month exchange rates length mismatch"
    try:
        prn_svc.print_exchange_rate_history(currency_codes[1])
    except ValueError as e:
        print(e)


def demo_roll_forward(container: Container) -> None:
    month_str = "2025-11"

    prn_svc: ReportService = container.resolve(ReportService)
    upd_svc: UpdateService = container.resolve(UpdateService)

    month = Month.parse(month_str)
    next_month = month.increment()

    print("Before roll forward:")
    curr_bal = prn_svc.get_month_balances(month)
    curr_sum = sum(b.amount for b in curr_bal)
    assert curr_sum == 277600, "Current month balances sum mismatch"
    print(f"Copying balances from {month} to {next_month}...")
    upd_svc.roll_balances_forward(month)
    print("After copying:")
    next_bal = prn_svc.get_month_balances(month)
    next_sum = sum(b.amount for b in next_bal)
    assert next_sum == 277600, "Next month balances sum mismatch"
    prn_svc.print_month_balances(next_month)


def main():
    container = build_sqlite_uow_container()

    demo_init(container)
    demo_accounts(container)
    demo_net_worth(container)
    demo_fetch_balance(container)
    demo_update_balance(container)
    demo_exchange_rate(container)
    demo_roll_forward(container)

    # DB connection singleton cleanup
    container.resolve(DBConnectionManager).close_connection()


if __name__ == "__main__":
    main()
