"""
Test services using CSV data files as input.
"""

import pytest
from nwtrack.admin import DBAdminService
from nwtrack.container import Container
from nwtrack.models import Month, Balance, NetWorth
from nwtrack.services import InitDataService, ReportService, UpdateService
from tests.test_repos import count_entries


def init_db_tables_w_entities(container: Container, entities: dict[str, list]) -> None:
    """Initialize database and load sample data."""
    container.resolve(DBAdminService).init_database()
    data_svc: InitDataService = container.resolve(InitDataService)
    data_svc._insert_entities(entities)


def init_db_tables_from_csv(container: Container, file_paths: dict[str, str]) -> None:
    """Initialize database and load sample data."""
    container.resolve(DBAdminService).init_database()
    data_svc: InitDataService = container.resolve(InitDataService)
    data_svc.insert_data_from_csv(file_paths)


def test_init_data_from_csv(
    test_container: Container, test_file_paths: dict[str, str]
) -> None:
    """Test initializing database and loading sample data from CSV files"""
    init_db_tables_from_csv(test_container, test_file_paths)
    cnts = count_entries(test_container)
    assert cnts["currencies"] == 3, "Expected 3 currencies"
    assert cnts["categories"] == 4, "Expected 4 categories"
    assert cnts["accounts"] == 4, "Expected 4 accounts"
    assert cnts["balances"] == 42, "Expected 42 balances"
    assert cnts["exchange_rates"] == 48, "Expected 48 exchange rates"


def test_init_data_entities(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test initializing database and loading sample data."""
    init_db_tables_w_entities(test_container, test_entities)
    cnts = count_entries(test_container)
    assert cnts["currencies"] == 3, "Expected 3 currencies"
    assert cnts["categories"] == 4, "Expected 4 categories"
    assert cnts["accounts"] == 4, "Expected 4 accounts"
    assert cnts["balances"] == 42, "Expected 42 balances"
    assert cnts["exchange_rates"] == 48, "Expected 48 exchange rates"


def test_accounts(test_container: Container, test_entities: dict[str, list]) -> None:
    """Test retrieving accounts."""
    init_db_tables_w_entities(test_container, test_entities)
    prn_svc: ReportService = test_container.resolve(ReportService)

    active_accounts = prn_svc.get_accounts(active_only=True)
    assert len(active_accounts) == 3, "Expecting 3 active accounts"
    assert active_accounts[-1].id == 3, "Expecting last active account ID == 3"
    assert active_accounts[-1].name == "credit_cards_1"

    all_accounts = prn_svc.get_accounts(active_only=False)
    assert len(all_accounts) == 4, "Expecting 4 total accounts"
    assert all_accounts[-1].id == 4, "Expecting last account ID == 4"
    assert all_accounts[-1].name == "mortgage_1"


def test_net_worth(test_container: Container, test_entities: dict[str, list]) -> None:
    """Test retrieving net worth."""
    month_str = "2025-11"

    init_db_tables_w_entities(test_container, test_entities)
    month = Month.parse(month_str)
    prn_svc: ReportService = test_container.resolve(ReportService)

    net_worth = prn_svc.get_net_worth(month=month)
    assert net_worth.month == month, "Net worth month mismatch"
    assert net_worth.assets == 700, "Net worth assets mismatch"
    assert net_worth.liabilities == 600, "Net worth liabilities mismatch"
    assert net_worth.net_worth == 100, "Net worth total mismatch"


def test_net_worth_hist(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test retrieving net worth."""
    init_db_tables_w_entities(test_container, test_entities)
    prn_svc: ReportService = test_container.resolve(ReportService)

    net_worth_hist = prn_svc.get_net_worth_history()
    assert len(net_worth_hist) == 12, "Net worth history length mismatch"
    assert isinstance(net_worth_hist[0], NetWorth), "Net worth history type mismatch"
    assert net_worth_hist[-1].month == Month(2025, 11)
    assert net_worth_hist[-1].net_worth == 100, "Net worth history last total mismatch"


def test_fetch_balance(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test fetching balances."""
    account_name = "bank_1_checking"
    month_str = "2025-10"

    init_db_tables_w_entities(test_container, test_entities)
    prn_svc: ReportService = test_container.resolve(ReportService)
    month = Month.parse(month_str)

    account_map = {acc.id: acc for acc in prn_svc.get_accounts()}
    assert len(account_map) == 3, "Account map length mismatch"
    assert account_map[2].name == "bank_2_savings", "Account map entry mismatch"

    single_bal = prn_svc.get_balance(month, account_name)
    assert single_bal.id == 37, "Balance id mismatch"
    assert account_map[single_bal.account_id].name == account_name
    assert single_bal.account_id == 1, "Balance account id mismatch"
    assert single_bal.month == month, "Balance month mismatch"
    assert single_bal.amount == 200, "Balance amount mismatch"


def test_balance_month(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test retrieving balances by month"""
    month_str = "2025-10"

    init_db_tables_w_entities(test_container, test_entities)
    prn_svc: ReportService = test_container.resolve(ReportService)
    month = Month.parse(month_str)

    month_bals = prn_svc.get_month_balances(month)
    assert len(month_bals) == 3, "Month balances length mismatch"
    assert isinstance(month_bals[0], Balance), "Month balances type mismatch"
    assert month_bals[0].month == month, "Month balances month mismatch"

    sample = prn_svc.get_balances_sample(5)
    assert len(sample) == 5, "Balances sample length mismatch"
    assert isinstance(sample[0], Balance), "Balances sample type mismatch"


def test_update_balance_account_name(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test updating a balance for a given account name."""
    account_name = "bank_1_checking"
    month_str = "2024-06"
    new_amount = 500

    init_db_tables_w_entities(test_container, test_entities)
    month = Month.parse(month_str)
    upd_svc: UpdateService = test_container.resolve(UpdateService)
    prn_svc: ReportService = test_container.resolve(ReportService)

    before = prn_svc.get_balance(month, account_name)
    assert before.amount == 300, "Pre-update balance amount mismatch"
    upd_svc.update_balance_account_name(
        account_name=account_name,
        month=month,
        new_amount=new_amount,
    )
    after = prn_svc.get_balance(month, account_name)
    assert after.amount == new_amount, "Post-update balance amount mismatch"


def test_exchange_rate(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test fetching exchange rates."""
    currency_codes = ["CNY", "EUR"]
    month_str = "2018-12"

    init_db_tables_w_entities(test_container, test_entities)
    prn_svc: ReportService = test_container.resolve(ReportService)
    month = Month.parse(month_str)

    rate = prn_svc.get_exchange_rate(month, currency_codes[0])
    assert rate is not None, "Exchange rate not found"
    assert rate.rate == 6.80, "Exchange rate value mismatch"


def test_exchange_rate_month(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test fetching exchange rates."""
    currency_codes = ["CNY", "EUR"]
    month_str = "2018-12"

    init_db_tables_w_entities(test_container, test_entities)
    prn_svc: ReportService = test_container.resolve(ReportService)
    month = Month.parse(month_str)

    rates = prn_svc.get_month_exchange_rates(month)
    assert len(rates) == 2, "Month exchange rates length mismatch"
    with pytest.raises(ValueError) as exc_info:
        prn_svc.print_exchange_rate_history(currency_codes[1])
    assert f"Currency '{currency_codes[1]}'" in str(exc_info.value)


def test_roll_forward(
    test_container: Container, test_entities: dict[str, list]
) -> None:
    """Test rolling balances forward to next month."""
    month_str = "2025-11"

    init_db_tables_w_entities(test_container, test_entities)
    prn_svc: ReportService = test_container.resolve(ReportService)
    upd_svc: UpdateService = test_container.resolve(UpdateService)

    month = Month.parse(month_str)
    next_month = month.increment()

    curr_bal = prn_svc.get_month_balances(month)
    curr_sum = sum(b.amount for b in curr_bal)
    assert curr_sum == 1300, "Current month balances sum mismatch"
    upd_svc.roll_balances_forward(month)
    next_bal = prn_svc.get_month_balances(next_month)
    next_sum = sum(b.amount for b in next_bal)
    assert next_sum == 1300, "Next month balances sum mismatch"
