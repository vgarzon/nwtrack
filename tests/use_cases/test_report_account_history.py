"""Tests for the shared single-account balance history use case."""

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.ports.schema import SchemaManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.application.use_cases.report_account_history import (
    ReportAccountBalanceHistory,
)
from nwtrack.bootstrap.container import Container
from nwtrack.domain.value_objects import Month
from nwtrack.infra.config.settings import Settings


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register the services needed to initialize test data."""
    return base_container.register(
        DBAdminService,
        lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
    )


def _use_case(container: Container) -> ReportAccountBalanceHistory:
    return ReportAccountBalanceHistory(uow=lambda: container.resolve(UnitOfWork))


def test_full_contiguous_range_computes_deltas_and_summary(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Account 1 has a balance for every month from 2024-06 to 2024-11."""
    init_db_tables_w_entities(configured_container, sample_entities)
    result = _use_case(configured_container).run(
        account_id=1,
        start_month=Month(2024, 6),
        end_month=Month(2024, 11),
    )

    assert result.success
    data = result.data
    assert data is not None
    assert [row.balance for row in data.rows] == [300, 300, 300, 200, 200, 200]
    assert [row.delta for row in data.rows] == [None, 0, 0, -100, 0, 0]

    assert data.summary is not None
    assert data.summary.min_balance == 200
    assert data.summary.max_balance == 300
    assert data.summary.average_balance == pytest.approx(250.0)
    assert data.summary.total_change == -100
    assert data.summary.first_month == Month(2024, 6)
    assert data.summary.last_month == Month(2024, 11)


def test_gap_months_are_blank_and_delta_skips_the_gap(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Account 3 has no balance records between 2024-11 and 2025-06.

    The gap months must show a null balance/delta, and the delta for the
    first month after the gap must be computed against the last *actual*
    balance (2024-11), not against zero or the immediately preceding month.
    """
    init_db_tables_w_entities(configured_container, sample_entities)
    result = _use_case(configured_container).run(
        account_id=3,
        start_month=Month(2024, 10),
        end_month=Month(2025, 7),
    )

    assert result.success
    data = result.data
    assert data is not None

    # Liability balances are stored as positive amounts (abs of the CSV values).
    by_month = {row.month: row for row in data.rows}
    assert by_month[Month(2024, 10)].balance == 1100
    assert by_month[Month(2024, 11)].balance == 800
    for month in [Month(2024, m) for m in (12,)] + [
        Month(2025, m) for m in (1, 2, 3, 4, 5)
    ]:
        assert by_month[month].balance is None
        assert by_month[month].delta is None
    assert by_month[Month(2025, 6)].balance == 500
    assert by_month[Month(2025, 6)].delta == -300  # 500 - 800, skipping the gap
    assert by_month[Month(2025, 7)].balance == 500
    assert by_month[Month(2025, 7)].delta == 0

    assert data.summary is not None
    assert data.summary.min_balance == 500
    assert data.summary.max_balance == 1100
    assert data.summary.total_change == -600  # 500 - 1100
    assert data.summary.first_month == Month(2024, 10)
    assert data.summary.last_month == Month(2025, 7)


def test_zero_record_range_returns_no_summary(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """A range with no balance records at all must not fabricate a summary."""
    init_db_tables_w_entities(configured_container, sample_entities)
    result = _use_case(configured_container).run(
        account_id=1,
        start_month=Month(2023, 1),
        end_month=Month(2023, 2),
    )

    assert result.success
    data = result.data
    assert data is not None
    assert all(row.balance is None for row in data.rows)
    assert data.summary is None


def test_single_record_range_has_no_delta_and_flat_summary(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """One record in range: no delta is computable; summary collapses to that value."""
    init_db_tables_w_entities(configured_container, sample_entities)
    result = _use_case(configured_container).run(
        account_id=1,
        start_month=Month(2024, 6),
        end_month=Month(2024, 6),
    )

    assert result.success
    data = result.data
    assert data is not None
    assert len(data.rows) == 1
    assert data.rows[0].balance == 300
    assert data.rows[0].delta is None

    assert data.summary is not None
    assert data.summary.min_balance == 300
    assert data.summary.max_balance == 300
    assert data.summary.average_balance == pytest.approx(300.0)
    assert data.summary.total_change == 0
    assert data.summary.first_month == Month(2024, 6)
    assert data.summary.last_month == Month(2024, 6)


def test_invalid_range_is_rejected(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """start_month after end_month must fail validation before querying."""
    init_db_tables_w_entities(configured_container, sample_entities)
    result = _use_case(configured_container).run(
        account_id=1,
        start_month=Month(2024, 11),
        end_month=Month(2024, 6),
    )

    assert not result.success
    assert result.data is None
    assert "earlier than or equal to" in result.error_message


def test_unknown_account_is_rejected(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """An account_id that does not exist must fail with a clear message."""
    init_db_tables_w_entities(configured_container, sample_entities)
    result = _use_case(configured_container).run(
        account_id=999,
        start_month=Month(2024, 6),
        end_month=Month(2024, 11),
    )

    assert not result.success
    assert result.data is None
    assert "999" in result.error_message


def test_result_includes_account_header_context(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """The result must carry account name, category, and currency for display."""
    init_db_tables_w_entities(configured_container, sample_entities)
    result = _use_case(configured_container).run(
        account_id=1,
        start_month=Month(2024, 6),
        end_month=Month(2024, 6),
    )

    assert result.success
    data = result.data
    assert data is not None
    assert data.account_id == 1
    assert data.account_name == "bank_1_checking"
    assert data.category_name == "checking"
    assert data.currency_code == "USD"
    assert data.institution_name is None
