"""Tests for the shared history aggregation use case."""

from collections.abc import Callable
from typing import cast

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    HistoryAggregationRequest,
    HistoryAggregationResult,
)
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases.report_history_aggregation import (
    ReportHistoryAggregation,
)
from nwtrack.domain.value_objects import Month


class FakeReportingQueries:
    """Test double for the shared reporting query port."""

    def __init__(
        self,
        *,
        range_currencies: list[str] | None = None,
        result: HistoryAggregationResult | None = None,
    ) -> None:
        self.range_currencies = range_currencies or []
        self.result = result
        self.range_currency_calls: list[tuple[Month, Month, AccountStatusScope]] = []
        self.aggregate_calls: list[HistoryAggregationRequest] = []

    def get_range_currencies(
        self,
        start_month: Month,
        end_month: Month,
        status_scope: AccountStatusScope,
    ) -> list[str]:
        self.range_currency_calls.append((start_month, end_month, status_scope))
        return list(self.range_currencies)

    def aggregate_history(
        self,
        request: HistoryAggregationRequest,
    ) -> HistoryAggregationResult:
        self.aggregate_calls.append(request)
        if self.result is None:
            raise AssertionError("result must be configured for aggregate_history")
        return self.result


class FakeUnitOfWork:
    """Context-manager test double exposing the reporting port."""

    def __init__(self, reporting: FakeReportingQueries) -> None:
        self.reporting = reporting
        self._reporting = reporting

    def __enter__(self) -> "FakeUnitOfWork":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None


def _build_use_case(reporting: FakeReportingQueries) -> ReportHistoryAggregation:
    """Create the use case with a typed fake unit-of-work factory."""
    uow_factory = cast(Callable[[], UnitOfWork], lambda: FakeUnitOfWork(reporting))
    return ReportHistoryAggregation(uow=uow_factory)


def test_request_defaults_status_scope_to_active() -> None:
    """The shared request should default to active-only aggregation."""
    request = HistoryAggregationRequest(
        start_month=Month(2025, 9),
        end_month=Month(2025, 11),
        dimension=AggregationDimension.CATEGORY,
    )

    assert request.status_scope == AccountStatusScope.ACTIVE


def test_run_rejects_reversed_range() -> None:
    """A history range must not end before it starts."""
    request = HistoryAggregationRequest(
        start_month=Month(2025, 11),
        end_month=Month(2025, 9),
        dimension=AggregationDimension.CATEGORY,
    )
    reporting = FakeReportingQueries()
    use_case = _build_use_case(reporting)

    result = use_case.run(request)

    assert not result.success
    assert "earlier than or equal to end month" in result.error_message
    assert reporting.range_currency_calls == []
    assert reporting.aggregate_calls == []


def test_run_rejects_mixed_currency_non_currency_aggregation() -> None:
    """Non-currency aggregation should fail fast for mixed-currency ranges."""
    request = HistoryAggregationRequest(
        start_month=Month(2025, 9),
        end_month=Month(2025, 11),
        dimension=AggregationDimension.TAG,
    )
    reporting = FakeReportingQueries(range_currencies=["CHF", "USD"])
    use_case = _build_use_case(reporting)

    result = use_case.run(request)

    assert not result.success
    assert "currency_code" in result.error_message
    assert reporting.range_currency_calls == [
        (Month(2025, 9), Month(2025, 11), AccountStatusScope.ACTIVE)
    ]
    assert reporting.aggregate_calls == []


def test_run_allows_single_currency_non_currency_aggregation() -> None:
    """Single-currency ranges should aggregate without an explicit filter."""
    request = HistoryAggregationRequest(
        start_month=Month(2025, 9),
        end_month=Month(2025, 11),
        dimension=AggregationDimension.INSTITUTION,
    )
    expected = HistoryAggregationResult(
        start_month=request.start_month,
        end_month=request.end_month,
        dimension=request.dimension,
        currency_code="USD",
        status_scope=request.status_scope,
        rows=[],
    )
    reporting = FakeReportingQueries(range_currencies=["USD"], result=expected)
    use_case = _build_use_case(reporting)

    result = use_case.run(request)

    assert result.success
    assert result.data == expected
    assert reporting.aggregate_calls == [request]


def test_run_skips_currency_validation_when_currency_filter_is_supplied() -> None:
    """An explicit currency filter should bypass mixed-currency rejection."""
    request = HistoryAggregationRequest(
        start_month=Month(2025, 9),
        end_month=Month(2025, 11),
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        status_scope=AccountStatusScope.ALL,
    )
    expected = HistoryAggregationResult(
        start_month=request.start_month,
        end_month=request.end_month,
        dimension=request.dimension,
        currency_code="USD",
        status_scope=request.status_scope,
        rows=[],
    )
    reporting = FakeReportingQueries(range_currencies=["CHF", "USD"], result=expected)
    use_case = _build_use_case(reporting)

    result = use_case.run(request)

    assert result.success
    assert result.data == expected
    assert reporting.range_currency_calls == []
    assert reporting.aggregate_calls == [request]


def test_run_skips_currency_validation_for_currency_aggregation() -> None:
    """Currency aggregation may aggregate all currencies without a filter."""
    request = HistoryAggregationRequest(
        start_month=Month(2025, 9),
        end_month=Month(2025, 11),
        dimension=AggregationDimension.CURRENCY,
    )
    expected = HistoryAggregationResult(
        start_month=request.start_month,
        end_month=request.end_month,
        dimension=request.dimension,
        currency_code=None,
        status_scope=request.status_scope,
        rows=[],
    )
    reporting = FakeReportingQueries(range_currencies=["CHF", "USD"], result=expected)
    use_case = _build_use_case(reporting)

    result = use_case.run(request)

    assert result.success
    assert result.data == expected
    assert reporting.range_currency_calls == []
    assert reporting.aggregate_calls == [request]
