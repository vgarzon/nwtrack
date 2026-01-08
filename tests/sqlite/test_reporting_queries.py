"""
Tests for reporting queries.
"""

from nwtrack.domain.value_objects import Month
from nwtrack.bootstrap.composition import build_data_services_container
from tests.helpers import init_db_tables_w_entities, _uow_factory
from nwtrack.application.dto import MonthlyCategoryBalance


def test_get_monthly_total_by_category(base_container, sample_entities) -> None:
    """Test getting total balance amount by category for a given month."""
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)
    month = Month(2025, 11)

    with _uow_factory(container) as uow:
        rows = uow._reporting.monthly_balance_total_by_category(month)

    for row in rows:
        print(type(row), row)

    assert isinstance(rows[0], MonthlyCategoryBalance)
