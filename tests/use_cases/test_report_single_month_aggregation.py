"""Tests for the shared single-month aggregation use case."""

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    SingleMonthAggregationRequest,
    SingleMonthAggregationResult,
)
from nwtrack.application.use_cases.report_single_month_aggregation import (
    ReportSingleMonthAggregation,
)
from nwtrack.domain.value_objects import Month


class FakeReportingQueries:
    """Test double for the shared reporting query port."""

    def __init__(
        self,
        *,
        month_currencies: list[str] | None = None,
        result: SingleMonthAggregationResult | None = None,
    ) -> None:
        self.month_currencies = month_currencies or []
        self.result = result
        self.currency_calls: list[tuple[Month, AccountStatusScope]] = []
        self.aggregate_calls: list[SingleMonthAggregationRequest] = []

    def get_month_currencies(
        self, month: Month, status_scope: AccountStatusScope
    ) -> list[str]:
        self.currency_calls.append((month, status_scope))
        return list(self.month_currencies)

    def aggregate_single_month(
        self, request: SingleMonthAggregationRequest
    ) -> SingleMonthAggregationResult:
        self.aggregate_calls.append(request)
        if self.result is None:
            raise AssertionError("result must be configured for aggregate_single_month")
        return self.result


class FakeUnitOfWork:
    """Context-manager test double exposing the reporting port."""

    def __init__(self, reporting: FakeReportingQueries) -> None:
        self._reporting = reporting

    def __enter__(self) -> "FakeUnitOfWork":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None


def test_request_defaults_status_scope_to_active() -> None:
    """The shared request should default to active-only aggregation."""
    request = SingleMonthAggregationRequest(
        month=Month(2025, 11),
        dimension=AggregationDimension.CATEGORY,
    )

    assert request.status_scope == AccountStatusScope.ACTIVE


def test_run_rejects_mixed_currency_non_currency_aggregation() -> None:
    """Non-currency aggregation should fail fast for mixed-currency months."""
    request = SingleMonthAggregationRequest(
        month=Month(2025, 11),
        dimension=AggregationDimension.TAG,
    )
    reporting = FakeReportingQueries(month_currencies=["CHF", "USD"])
    use_case = ReportSingleMonthAggregation(uow=lambda: FakeUnitOfWork(reporting))

    result = use_case.run(request)

    assert not result.success
    assert "currency_code" in result.error_message
    assert reporting.currency_calls == [(Month(2025, 11), AccountStatusScope.ACTIVE)]
    assert reporting.aggregate_calls == []


def test_run_allows_single_currency_non_currency_aggregation() -> None:
    """Single-currency months should aggregate without an explicit filter."""
    request = SingleMonthAggregationRequest(
        month=Month(2025, 11),
        dimension=AggregationDimension.INSTITUTION,
    )
    expected = SingleMonthAggregationResult(
        month=request.month,
        dimension=request.dimension,
        currency_code="USD",
        status_scope=request.status_scope,
        groups=[],
    )
    reporting = FakeReportingQueries(month_currencies=["USD"], result=expected)
    use_case = ReportSingleMonthAggregation(uow=lambda: FakeUnitOfWork(reporting))

    result = use_case.run(request)

    assert result.success
    assert result.data == expected
    assert reporting.aggregate_calls == [request]


def test_run_skips_currency_validation_when_currency_filter_is_supplied() -> None:
    """An explicit currency filter should bypass mixed-currency rejection."""
    request = SingleMonthAggregationRequest(
        month=Month(2025, 11),
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        status_scope=AccountStatusScope.ALL,
    )
    expected = SingleMonthAggregationResult(
        month=request.month,
        dimension=request.dimension,
        currency_code="USD",
        status_scope=request.status_scope,
        groups=[],
    )
    reporting = FakeReportingQueries(month_currencies=["CHF", "USD"], result=expected)
    use_case = ReportSingleMonthAggregation(uow=lambda: FakeUnitOfWork(reporting))

    result = use_case.run(request)

    assert result.success
    assert result.data == expected
    assert reporting.currency_calls == []
    assert reporting.aggregate_calls == [request]


def test_run_skips_currency_validation_for_currency_aggregation() -> None:
    """Currency aggregation may aggregate all currencies without a filter."""
    request = SingleMonthAggregationRequest(
        month=Month(2025, 11),
        dimension=AggregationDimension.CURRENCY,
    )
    expected = SingleMonthAggregationResult(
        month=request.month,
        dimension=request.dimension,
        currency_code=None,
        status_scope=request.status_scope,
        groups=[],
    )
    reporting = FakeReportingQueries(month_currencies=["CHF", "USD"], result=expected)
    use_case = ReportSingleMonthAggregation(uow=lambda: FakeUnitOfWork(reporting))

    result = use_case.run(request)

    assert result.success
    assert result.data == expected
    assert reporting.currency_calls == []
    assert reporting.aggregate_calls == [request]
