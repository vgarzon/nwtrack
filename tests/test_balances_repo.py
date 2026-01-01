"""
Test suite for Balances repository operations
"""

from nwtrack.container import Container
from nwtrack.unitofwork import UnitOfWork
from tests.test_services import init_db_tables_w_entities
from nwtrack.models import Month

# TODO: add tests for other balance repo methods


def uow_factory(test_container: Container) -> UnitOfWork:
    return test_container.resolve(UnitOfWork)


def test_count_balances_entries(test_container, test_entities) -> None:
    """Test counting entries in the balances repository."""
    init_db_tables_w_entities(test_container, test_entities)

    with uow_factory(test_container) as uow:
        cnt = uow.balances.count()

    assert cnt == 42


def test_count_balances_per_month(test_container, test_entities) -> None:
    """Test counting balances entries per month."""
    init_db_tables_w_entities(test_container, test_entities)

    with uow_factory(test_container) as uow:
        cnts = uow.balances.count_per_month()

    assert len(cnts) == 12
    earliest = min(cnts, key=lambda x: x[0])
    assert earliest == (Month(2024, 6), 4)
    latest = max(cnts, key=lambda x: x[0])
    assert latest == (Month(2025, 11), 3)
