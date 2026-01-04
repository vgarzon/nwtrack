"""
Test suite for Balances repository operations
"""

from nwtrack.compose import build_data_services_container
from nwtrack.container import Container
from nwtrack.models import Month
from nwtrack.unitofwork import UnitOfWork
from tests.test_services import init_db_tables_w_entities

# TODO: add tests for other balance repo methods


def uow_factory(container: Container) -> UnitOfWork:
    return container.resolve(UnitOfWork)


def test_insert_single_balance(test_container, test_entities) -> None:
    """Test inserting a single balance entry."""
    container = build_data_services_container(test_container)
    init_db_tables_w_entities(container, test_entities)
    new_balance_data = {
        "id": 0,  # will be set by the database
        "account_id": 1,
        "month": "2025-12",
        "amount": 300,
    }
    month = new_balance_data["month"]
    account_id = new_balance_data["account_id"]

    with uow_factory(container) as uow:
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


def test_count_balances_entries(test_container, test_entities) -> None:
    """Test counting entries in the balances repository."""
    container = build_data_services_container(test_container)
    init_db_tables_w_entities(container, test_entities)

    with uow_factory(container) as uow:
        cnt = uow.balances.count()

    assert cnt == 42


def test_count_balances_per_month(test_container, test_entities) -> None:
    """Test counting balances entries per month."""
    container = build_data_services_container(test_container)
    init_db_tables_w_entities(container, test_entities)

    with uow_factory(container) as uow:
        cnts = uow.balances.count_per_month()

    assert len(cnts) == 12
    earliest = min(cnts, key=lambda x: x[0])
    assert earliest == (Month(2024, 6), 4)
    latest = max(cnts, key=lambda x: x[0])
    assert latest == (Month(2025, 11), 3)
