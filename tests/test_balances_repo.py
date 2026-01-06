"""
Test suite for Balances repository operations
"""

from nwtrack.compose import build_data_services_container
from nwtrack.domain.value_objects import Month
from tests.helpers import init_db_tables_w_entities, _uow_factory

# TODO: add tests for other balance repo methods


def test_insert_single_balance(base_container, sample_entities) -> None:
    """Test inserting a single balance entry."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)
    account_id = 1
    month_str = "2025-12"
    month = Month.parse(month_str)
    new_balance_data = {
        "id": 0,  # will be set by the database
        "account_id": account_id,
        "month": month_str,
        "amount": 300,
    }
    with _uow_factory(container) as uow:
        new_balance = uow.balances.hydrate(new_balance_data)
        last_id = uow.balances.insert(new_balance)
        inserted_balance = uow.balances.get_by_account_id(
            month=month, account_id=account_id
        )
    print(last_id)
    assert inserted_balance is not None
    assert inserted_balance.account_id == new_balance_data["account_id"]
    assert str(inserted_balance.month) == new_balance_data["month"]
    assert inserted_balance.amount == new_balance_data["amount"]


def test_count_balances_entries(base_container, sample_entities) -> None:
    """Test counting entries in the balances repository."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        cnt = uow.balances.count()

    assert cnt == 42


def test_count_balances_per_month(base_container, sample_entities) -> None:
    """Test counting balances entries per month."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)

    with _uow_factory(container) as uow:
        cnts = uow.balances.count_per_month()

    assert len(cnts) == 12
    earliest = min(cnts, key=lambda x: x[0])
    assert earliest == (Month(2024, 6), 4)
    latest = max(cnts, key=lambda x: x[0])
    assert latest == (Month(2025, 11), 3)
