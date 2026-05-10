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

    def __init__(
        self,
        balance_counts: list[tuple[Month, int]] | None = None,
        month_currencies: dict[tuple[Month, AccountStatusScope], list[str]] | None = None,
    ) -> None:
        self.balance_counts = balance_counts or []
        self.month_currencies = month_currencies or {}

    def get_balance_count_per_month(self) -> list[tuple[Month, int]]:
        return list(self.balance_counts)

    def get_month_currencies(
        self,
        month: Month,
        status_scope: AccountStatusScope = AccountStatusScope.ACTIVE,
    ) -> list[str]:
        return list(self.month_currencies.get((month, status_scope), []))


class RecordingPresenter:
    """Presenter double that records report workflow interactions."""

    def __init__(self) -> None:
        self.header_calls = 0
        self.errors: list[str] = []
        self.no_data_calls: list[tuple[Month, AggregationDimension, str | None]] = []
        self.displayed_results: list[SingleMonthAggregationResult] = []
        self.month_prompt_calls: list[list[tuple[Month, int]]] = []
        self.dimension_prompt_calls = 0
        self.currency_prompt_calls: list[list[str]] = []
        self.selected_month: Month | None = None
        self.selected_dimension: AggregationDimension | None = None
        self.selected_currency: str | None = None
        self.no_month_selected_calls = 0
        self.no_dimension_selected_calls = 0
        self.no_currency_selected_calls = 0

    def show_header(self) -> None:
        self.header_calls += 1

    def prompt_for_month_choice(self, balance_counts):
        self.month_prompt_calls.append(list(balance_counts))
        return self.selected_month

    def prompt_for_dimension_choice(self):
        self.dimension_prompt_calls += 1
        return self.selected_dimension

    def prompt_for_currency_choice(self, currencies):
        self.currency_prompt_calls.append(list(currencies))
        return self.selected_currency

    def show_no_month_selected_message(self) -> None:
        self.no_month_selected_calls += 1

    def show_no_dimension_selected_message(self) -> None:
        self.no_dimension_selected_calls += 1

    def show_no_currency_selected_message(self) -> None:
        self.no_currency_selected_calls += 1

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


def test_run_prompts_for_month_when_missing() -> None:
    """The workflow should prompt for a month when the flag is omitted."""
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
    fetcher = FakeFetchService(
        balance_counts=[
            (Month(2025, 9), 3),
            (Month(2025, 10), 4),
            (Month(2025, 11), 5),
            (Month(2025, 8), 2),
        ]
    )
    aggregation_report = FakeAggregationReport(
        OperationResult(success=True, data=expected)
    )
    presenter = RecordingPresenter()
    presenter.selected_month = month
    workflow = SingleMonthAggregatedBalanceReport(
        fetcher=fetcher,
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        month=None,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
    )

    assert result.success
    assert presenter.month_prompt_calls == [
        [(Month(2025, 11), 5), (Month(2025, 10), 4), (Month(2025, 9), 3)]
    ]
    assert aggregation_report.requests[0].month == month


def test_run_prompts_for_dimension_when_missing() -> None:
    """The workflow should prompt for a dimension when the flag is omitted."""
    month = Month(2025, 11)
    expected = SingleMonthAggregationResult(
        month=month,
        dimension=AggregationDimension.SIDE,
        currency_code="USD",
        status_scope=AccountStatusScope.ACTIVE,
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
    presenter.selected_dimension = AggregationDimension.SIDE
    workflow = SingleMonthAggregatedBalanceReport(
        fetcher=FakeFetchService(),
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        month=month,
        dimension=None,
        currency_code="USD",
    )

    assert result.success
    assert presenter.dimension_prompt_calls == 1
    assert aggregation_report.requests[0].dimension == AggregationDimension.SIDE


def test_run_prompts_for_currency_for_interactive_mixed_currency_request() -> None:
    """Interactive mixed-currency non-currency aggregation should prompt for currency."""
    month = Month(2025, 11)
    expected = SingleMonthAggregationResult(
        month=month,
        dimension=AggregationDimension.CATEGORY,
        currency_code="CHF",
        status_scope=AccountStatusScope.ACTIVE,
        groups=[
            SingleMonthAggregationGroup(
                group_key="checking",
                label="checking",
                amount=700,
                currency_code="CHF",
            )
        ],
    )
    fetcher = FakeFetchService(
        month_currencies={(month, AccountStatusScope.ACTIVE): ["CHF", "USD"]}
    )
    aggregation_report = FakeAggregationReport(
        OperationResult(success=True, data=expected)
    )
    presenter = RecordingPresenter()
    presenter.selected_currency = "CHF"
    workflow = SingleMonthAggregatedBalanceReport(
        fetcher=fetcher,
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        month=month,
        dimension=AggregationDimension.CATEGORY,
        currency_code=None,
    )

    assert result.success
    assert presenter.currency_prompt_calls == [["CHF", "USD"]]
    assert aggregation_report.requests[0].currency_code == "CHF"


def test_run_fails_cleanly_for_non_interactive_mixed_currency_request() -> None:
    """Non-interactive mixed-currency non-currency requests should require --currency."""
    month = Month(2025, 11)
    aggregation_report = FakeAggregationReport(
        OperationResult(
            success=False,
            error_message="shared use case should not be called",
        )
    )
    presenter = RecordingPresenter()
    workflow = SingleMonthAggregatedBalanceReport(
        fetcher=FakeFetchService(
            month_currencies={(month, AccountStatusScope.ACTIVE): ["CHF", "USD"]}
        ),
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        month=month,
        dimension=AggregationDimension.CATEGORY,
        currency_code=None,
        allow_interactive=False,
    )

    assert not result.success
    assert presenter.errors == [
        "Aggregation requires one currency. Provide --currency for mixed-currency months."
    ]
    assert aggregation_report.requests == []


def test_run_quits_cleanly_when_month_selection_is_cancelled() -> None:
    """Cancelling month selection should exit without running the aggregation."""
    presenter = RecordingPresenter()
    workflow = SingleMonthAggregatedBalanceReport(
        fetcher=FakeFetchService(balance_counts=[(Month(2025, 11), 5)]),
        aggregation_report=FakeAggregationReport(
            OperationResult(success=True, data=None)
        ),
        presenter=presenter,
    )

    result = workflow.run(
        month=None,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
    )

    assert not result.success
    assert presenter.no_month_selected_calls == 1


def test_run_quits_cleanly_when_dimension_selection_is_cancelled() -> None:
    """Cancelling dimension selection should exit without running the aggregation."""
    presenter = RecordingPresenter()
    workflow = SingleMonthAggregatedBalanceReport(
        fetcher=FakeFetchService(),
        aggregation_report=FakeAggregationReport(
            OperationResult(success=True, data=None)
        ),
        presenter=presenter,
    )

    result = workflow.run(
        month=Month(2025, 11),
        dimension=None,
        currency_code="USD",
    )

    assert not result.success
    assert presenter.no_dimension_selected_calls == 1


def test_run_quits_cleanly_when_currency_selection_is_cancelled() -> None:
    """Cancelling currency selection should exit without running the aggregation."""
    month = Month(2025, 11)
    presenter = RecordingPresenter()
    workflow = SingleMonthAggregatedBalanceReport(
        fetcher=FakeFetchService(
            month_currencies={(month, AccountStatusScope.ACTIVE): ["CHF", "USD"]}
        ),
        aggregation_report=FakeAggregationReport(
            OperationResult(success=True, data=None)
        ),
        presenter=presenter,
    )

    result = workflow.run(
        month=month,
        dimension=AggregationDimension.CATEGORY,
        currency_code=None,
    )

    assert not result.success
    assert presenter.no_currency_selected_calls == 1
