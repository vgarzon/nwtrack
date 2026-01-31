"""
Tests for reporting queries.
"""

from tests.helpers import _uow_factory, init_db_tables_w_entities

from nwtrack.application.dto import MonthlyCategoryBalance
from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.domain.value_objects import Month


def test_get_monthly_total_by_category(base_container, sample_entities) -> None:
    """Test getting total balance amount by category for a given month."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)
    month = Month(2025, 11)

    with _uow_factory(container) as uow:
        rows = uow._reporting.monthly_balance_total_by_category(month)
    assert len(rows) == 3

    checking = next((row for row in rows if "checking" in row.category.name), None)
    assert checking is not None
    assert isinstance(checking, MonthlyCategoryBalance)
    assert checking.month == month
    assert checking.category.name == "checking"
    assert checking.amount == 200
