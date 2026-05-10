"""Tests for the dedicated single-month aggregated balance report workflow."""

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    OperationResult,
    SingleMonthAggregationGroup,
    SingleMonthAggregationRequest,
    SingleMonthAggregationResult,
)
from nwtrack.application.use_cases.report_balances_aggregate import (
    SingleMonthAggregatedBalanceReport,
)
from nwtrack.domain.value_objects import Month


class FakeFetchService:
    """Minimal fetch service double for aggregated report tests."""


class RecordingPresenter:
    """Presenter double that records report workflow interactions."""

    def __init__(self) -> None:
        self.header_calls = 0
        self.errors: list[str] = []
        self.no_data_calls: list[tuple[Month, AggregationDimension, str | None]] = []
        self.displayed_results: list[SingleMonthAggregationResult] = []

    def show_header(self) -> None:
        self.header_calls += 1

    def prompt_for_month_choice(self, balance_counts):  # pragma: no cover - unused here
        raise AssertionError("prompt_for_month_choice should not be used in this test")

    def prompt_for_dimension_choice(self):  # pragma: no cover - unused here
        raise AssertionError(
            "prompt_for_dimension_choice should not be used in this test"
        )

    def prompt_for_currency_choice(self, currencies):  # pragma: no cover - unused here
        raise AssertionError(
            "prompt_for_currency_choice should not be used in this test"
        )

    def show_no_month_selected_message(self) -> None:  # pragma: no cover - unused here
        raise AssertionError(
            "show_no_month_selected_message should not be used in this test"
        )

    def show_no_dimension_selected_message(
        self,
    ) -> None:  # pragma: no cover - unused here
        raise AssertionError(
            "show_no_dimension_selected_message should not be used in this test"
        )

    def show_no_currency_selected_message(
        self,
    ) -> None:  # pragma: no cover - unused here
        raise AssertionError(
            "show_no_currency_selected_message should not be used in this test"
        )

    def show_no_data_message(
        self,
        month: Month,
        dimension: AggregationDimension,
        status_scope: AccountStatusScope,
        currency_code: str | None,
    ) -> None:
        self.no_data_calls.append((month, dimension, currency_code))

    def display_aggregation_report(
        self,
        result: SingleMonthAggregationResult,
    ) -> None:
        self.displayed_results.append(result)

    def show_error(self, message: str) -> None:
        self.errors.append(message)


class FakeAggregationReport:
    """Use-case double for the shared aggregation layer."""

    def __init__(self, result: OperationResult[SingleMonthAggregationResult]) -> None:
        self.result = result
        self.requests: list[SingleMonthAggregationRequest] = []

    def run(
        self,
        request: SingleMonthAggregationRequest,
    ) -> OperationResult[SingleMonthAggregationResult]:
        self.requests.append(request)
        return self.result


def test_run_passes_explicit_request_to_shared_aggregation_use_case() -> None:
    """The dedicated report should wrap and forward the shared aggregation request."""
    month = Month(2025, 11)
    expected = SingleMonthAggregationResult(
        month=month,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        status_scope=AccountStatusScope.ACTIVE,
        groups=[
            SingleMonthAggregationGroup(
                group_key="checking",
                label="checking",
                amount=200,
                currency_code="USD",
            )
        ],
    )
    aggregation_report = FakeAggregationReport(
        OperationResult(success=True, data=expected)
    )
    presenter = RecordingPresenter()
    workflow = SingleMonthAggregatedBalanceReport(
        fetcher=FakeFetchService(),
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        month=month,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        status_scope=AccountStatusScope.ACTIVE,
        allow_interactive=False,
    )

    assert result.success
    assert aggregation_report.requests == [
        SingleMonthAggregationRequest(
            month=month,
            dimension=AggregationDimension.CATEGORY,
            currency_code="USD",
            status_scope=AccountStatusScope.ACTIVE,
        )
    ]
    assert presenter.header_calls == 1
    assert presenter.displayed_results == [expected]
    assert presenter.errors == []


def test_run_preserves_requested_status_scope() -> None:
    """The dedicated report should forward the selected status scope unchanged."""
    month = Month(2025, 11)
    expected = SingleMonthAggregationResult(
        month=month,
        dimension=AggregationDimension.SIDE,
        currency_code="USD",
        status_scope=AccountStatusScope.ALL,
        groups=[
            SingleMonthAggregationGroup(
                group_key="asset",
                label="asset",
                amount=700,
                currency_code="USD",
            )
        ],
    )
    aggregation_report = FakeAggregationReport(
        OperationResult(success=True, data=expected)
    )
    presenter = RecordingPresenter()
    workflow = SingleMonthAggregatedBalanceReport(
        fetcher=FakeFetchService(),
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        month=month,
        dimension=AggregationDimension.SIDE,
        currency_code="USD",
        status_scope=AccountStatusScope.ALL,
        allow_interactive=False,
    )

    assert result.success
    assert aggregation_report.requests[0].status_scope == AccountStatusScope.ALL
    assert presenter.displayed_results == [expected]


def test_run_shows_no_data_message_for_empty_results() -> None:
    """Valid empty aggregation results should not be treated as workflow failures."""
    month = Month(2025, 11)
    expected = SingleMonthAggregationResult(
        month=month,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        status_scope=AccountStatusScope.ACTIVE,
        groups=[],
    )
    aggregation_report = FakeAggregationReport(
        OperationResult(success=True, data=expected)
    )
    presenter = RecordingPresenter()
    workflow = SingleMonthAggregatedBalanceReport(
        fetcher=FakeFetchService(),
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        month=month,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        status_scope=AccountStatusScope.ACTIVE,
        allow_interactive=False,
    )

    assert result.success
    assert presenter.no_data_calls == [(month, AggregationDimension.CATEGORY, "USD")]
    assert presenter.displayed_results == []
    assert presenter.errors == []
