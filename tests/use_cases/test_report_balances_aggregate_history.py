"""Tests for the dedicated history aggregated balance report workflow."""

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    HistoryAggregationRequest,
    HistoryAggregationResult,
    HistoryAggregationRow,
    OperationResult,
)
from nwtrack.application.use_cases.report_balances_aggregate_history import (
    HistoryAggregatedBalanceReport,
)
from nwtrack.domain.value_objects import Month


class FakeFetchService:
    """Minimal fetch service double for history aggregated report tests."""

    def __init__(
        self,
        balance_counts: list[tuple[Month, int]] | None = None,
        range_currencies: (
            dict[tuple[Month, Month, AccountStatusScope], list[str]] | None
        ) = None,
    ) -> None:
        self.balance_counts = balance_counts or []
        self.range_currencies = range_currencies or {}

    def get_balance_count_per_month(self) -> list[tuple[Month, int]]:
        return list(self.balance_counts)

    def get_range_currencies(
        self,
        start_month: Month,
        end_month: Month,
        status_scope: AccountStatusScope = AccountStatusScope.ACTIVE,
    ) -> list[str]:
        return list(
            self.range_currencies.get((start_month, end_month, status_scope), [])
        )


class RecordingPresenter:
    """Presenter double that records history report workflow interactions."""

    def __init__(self) -> None:
        self.header_calls = 0
        self.errors: list[str] = []
        self.no_data_calls: list[
            tuple[Month, Month, AggregationDimension, str | None]
        ] = []
        self.displayed_results: list[HistoryAggregationResult] = []
        self.start_month_prompt_calls: list[list[tuple[Month, int]]] = []
        self.end_month_prompt_calls: list[list[tuple[Month, int]]] = []
        self.dimension_prompt_calls = 0
        self.currency_prompt_calls: list[list[str]] = []
        self.selected_months: list[Month | None] = []
        self.selected_dimension: AggregationDimension | None = None
        self.selected_currency: str | None = None
        self.no_start_month_selected_calls = 0
        self.no_end_month_selected_calls = 0
        self.no_dimension_selected_calls = 0
        self.no_currency_selected_calls = 0

    def show_header(self) -> None:
        self.header_calls += 1

    def prompt_for_start_month_choice(self, balance_counts):
        self.start_month_prompt_calls.append(list(balance_counts))
        if not self.selected_months:
            return None
        return self.selected_months.pop(0)

    def prompt_for_end_month_choice(self, balance_counts):
        self.end_month_prompt_calls.append(list(balance_counts))
        if not self.selected_months:
            return None
        return self.selected_months.pop(0)

    def prompt_for_dimension_choice(self):
        self.dimension_prompt_calls += 1
        return self.selected_dimension

    def prompt_for_currency_choice(self, currencies):
        self.currency_prompt_calls.append(list(currencies))
        return self.selected_currency

    def show_no_start_month_selected_message(self) -> None:
        self.no_start_month_selected_calls += 1

    def show_no_end_month_selected_message(self) -> None:
        self.no_end_month_selected_calls += 1

    def show_no_dimension_selected_message(self) -> None:
        self.no_dimension_selected_calls += 1

    def show_no_currency_selected_message(self) -> None:
        self.no_currency_selected_calls += 1

    def show_no_data_message(
        self,
        start_month: Month,
        end_month: Month,
        dimension: AggregationDimension,
        status_scope: AccountStatusScope,
        currency_code: str | None,
    ) -> None:
        self.no_data_calls.append((start_month, end_month, dimension, currency_code))

    def display_history_aggregation_report(
        self,
        result: HistoryAggregationResult,
    ) -> None:
        self.displayed_results.append(result)

    def show_error(self, message: str) -> None:
        self.errors.append(message)


class FakeAggregationReport:
    """Use-case double for the shared history aggregation layer."""

    def __init__(self, result: OperationResult[HistoryAggregationResult]) -> None:
        self.result = result
        self.requests: list[HistoryAggregationRequest] = []

    def run(
        self,
        request: HistoryAggregationRequest,
    ) -> OperationResult[HistoryAggregationResult]:
        self.requests.append(request)
        return self.result


def _build_result(
    start_month: Month,
    end_month: Month,
    dimension: AggregationDimension,
    currency_code: str | None,
    status_scope: AccountStatusScope,
    rows: list[HistoryAggregationRow],
) -> HistoryAggregationResult:
    return HistoryAggregationResult(
        start_month=start_month,
        end_month=end_month,
        dimension=dimension,
        currency_code=currency_code,
        status_scope=status_scope,
        rows=rows,
    )


def test_run_passes_explicit_request_to_shared_aggregation_use_case() -> None:
    """The dedicated history report should wrap and forward the shared request."""
    start_month = Month(2025, 9)
    end_month = Month(2025, 11)
    expected = _build_result(
        start_month,
        end_month,
        AggregationDimension.CATEGORY,
        "USD",
        AccountStatusScope.ACTIVE,
        [
            HistoryAggregationRow(
                month=start_month,
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
    workflow = HistoryAggregatedBalanceReport(
        fetcher=FakeFetchService(),
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        start_month=start_month,
        end_month=end_month,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        status_scope=AccountStatusScope.ACTIVE,
        allow_interactive=False,
    )

    assert result.success
    assert aggregation_report.requests == [
        HistoryAggregationRequest(
            start_month=start_month,
            end_month=end_month,
            dimension=AggregationDimension.CATEGORY,
            currency_code="USD",
            status_scope=AccountStatusScope.ACTIVE,
        )
    ]
    assert presenter.header_calls == 1
    assert presenter.displayed_results == [expected]
    assert presenter.errors == []


def test_run_preserves_requested_status_scope() -> None:
    """The dedicated history report should forward the selected status scope."""
    start_month = Month(2025, 9)
    end_month = Month(2025, 11)
    expected = _build_result(
        start_month,
        end_month,
        AggregationDimension.SIDE,
        "USD",
        AccountStatusScope.ALL,
        [
            HistoryAggregationRow(
                month=start_month,
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
    workflow = HistoryAggregatedBalanceReport(
        fetcher=FakeFetchService(),
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        start_month=start_month,
        end_month=end_month,
        dimension=AggregationDimension.SIDE,
        currency_code="USD",
        status_scope=AccountStatusScope.ALL,
        allow_interactive=False,
    )

    assert result.success
    assert aggregation_report.requests[0].status_scope == AccountStatusScope.ALL
    assert presenter.displayed_results == [expected]


def test_run_shows_no_data_message_for_empty_results() -> None:
    """Valid empty history results should not be treated as workflow failures."""
    start_month = Month(2025, 9)
    end_month = Month(2025, 11)
    expected = _build_result(
        start_month,
        end_month,
        AggregationDimension.CATEGORY,
        "USD",
        AccountStatusScope.ACTIVE,
        [],
    )
    aggregation_report = FakeAggregationReport(
        OperationResult(success=True, data=expected)
    )
    presenter = RecordingPresenter()
    workflow = HistoryAggregatedBalanceReport(
        fetcher=FakeFetchService(),
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        start_month=start_month,
        end_month=end_month,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        status_scope=AccountStatusScope.ACTIVE,
        allow_interactive=False,
    )

    assert result.success
    assert presenter.no_data_calls == [
        (start_month, end_month, AggregationDimension.CATEGORY, "USD")
    ]
    assert presenter.displayed_results == []
    assert presenter.errors == []


def test_run_prompts_for_start_month_when_missing() -> None:
    """The workflow should prompt for a start month when the flag is omitted."""
    start_month = Month(2025, 9)
    end_month = Month(2025, 11)
    expected = _build_result(
        start_month,
        end_month,
        AggregationDimension.CATEGORY,
        "USD",
        AccountStatusScope.ACTIVE,
        [
            HistoryAggregationRow(
                month=start_month,
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
    presenter.selected_months = [start_month]
    workflow = HistoryAggregatedBalanceReport(
        fetcher=fetcher,
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        start_month=None,
        end_month=end_month,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
    )

    assert result.success
    assert presenter.start_month_prompt_calls == [
        [(Month(2025, 11), 5), (Month(2025, 10), 4), (Month(2025, 9), 3)]
    ]
    assert presenter.end_month_prompt_calls == []
    assert aggregation_report.requests[0].start_month == start_month


def test_run_prompts_for_end_month_when_missing() -> None:
    """The workflow should prompt for an end month when the flag is omitted."""
    start_month = Month(2025, 9)
    end_month = Month(2025, 11)
    expected = _build_result(
        start_month,
        end_month,
        AggregationDimension.CATEGORY,
        "USD",
        AccountStatusScope.ACTIVE,
        [
            HistoryAggregationRow(
                month=end_month,
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
    presenter.selected_months = [end_month]
    workflow = HistoryAggregatedBalanceReport(
        fetcher=fetcher,
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        start_month=start_month,
        end_month=None,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
    )

    assert result.success
    assert presenter.start_month_prompt_calls == []
    assert presenter.end_month_prompt_calls == [
        [(Month(2025, 11), 5), (Month(2025, 10), 4), (Month(2025, 9), 3)]
    ]
    assert aggregation_report.requests[0].end_month == end_month


def test_run_uses_distinct_start_and_end_month_prompts() -> None:
    """The workflow should use separate presenter hooks for start and end month."""
    start_month = Month(2025, 9)
    end_month = Month(2025, 11)
    expected = _build_result(
        start_month,
        end_month,
        AggregationDimension.CATEGORY,
        "USD",
        AccountStatusScope.ACTIVE,
        [
            HistoryAggregationRow(
                month=start_month,
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
        ]
    )
    aggregation_report = FakeAggregationReport(
        OperationResult(success=True, data=expected)
    )
    presenter = RecordingPresenter()
    presenter.selected_months = [start_month, end_month]
    workflow = HistoryAggregatedBalanceReport(
        fetcher=fetcher,
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        start_month=None,
        end_month=None,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
    )

    assert result.success
    assert len(presenter.start_month_prompt_calls) == 1
    assert len(presenter.end_month_prompt_calls) == 1


def test_run_prompts_for_dimension_when_missing() -> None:
    """The workflow should prompt for a dimension when the flag is omitted."""
    start_month = Month(2025, 9)
    end_month = Month(2025, 11)
    expected = _build_result(
        start_month,
        end_month,
        AggregationDimension.SIDE,
        "USD",
        AccountStatusScope.ACTIVE,
        [
            HistoryAggregationRow(
                month=start_month,
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
    workflow = HistoryAggregatedBalanceReport(
        fetcher=FakeFetchService(),
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        start_month=start_month,
        end_month=end_month,
        dimension=None,
        currency_code="USD",
    )

    assert result.success
    assert presenter.dimension_prompt_calls == 1
    assert aggregation_report.requests[0].dimension == AggregationDimension.SIDE


def test_run_prompts_for_currency_for_interactive_mixed_currency_request() -> None:
    """Interactive mixed-currency history requests should prompt for currency."""
    start_month = Month(2025, 9)
    end_month = Month(2025, 11)
    expected = _build_result(
        start_month,
        end_month,
        AggregationDimension.CATEGORY,
        "CHF",
        AccountStatusScope.ACTIVE,
        [
            HistoryAggregationRow(
                month=start_month,
                group_key="checking",
                label="checking",
                amount=700,
                currency_code="CHF",
            )
        ],
    )
    fetcher = FakeFetchService(
        range_currencies={
            (start_month, end_month, AccountStatusScope.ACTIVE): ["CHF", "USD"]
        }
    )
    aggregation_report = FakeAggregationReport(
        OperationResult(success=True, data=expected)
    )
    presenter = RecordingPresenter()
    presenter.selected_currency = "CHF"
    workflow = HistoryAggregatedBalanceReport(
        fetcher=fetcher,
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        start_month=start_month,
        end_month=end_month,
        dimension=AggregationDimension.CATEGORY,
        currency_code=None,
    )

    assert result.success
    assert presenter.currency_prompt_calls == [["CHF", "USD"]]
    assert aggregation_report.requests[0].currency_code == "CHF"


def test_run_fails_cleanly_for_non_interactive_mixed_currency_request() -> None:
    """Non-interactive mixed-currency history requests should require --currency."""
    start_month = Month(2025, 9)
    end_month = Month(2025, 11)
    aggregation_report = FakeAggregationReport(
        OperationResult(
            success=False,
            error_message="shared use case should not be called",
        )
    )
    presenter = RecordingPresenter()
    workflow = HistoryAggregatedBalanceReport(
        fetcher=FakeFetchService(
            range_currencies={
                (start_month, end_month, AccountStatusScope.ACTIVE): ["CHF", "USD"]
            }
        ),
        aggregation_report=aggregation_report,
        presenter=presenter,
    )

    result = workflow.run(
        start_month=start_month,
        end_month=end_month,
        dimension=AggregationDimension.CATEGORY,
        currency_code=None,
        allow_interactive=False,
    )

    assert not result.success
    assert presenter.errors == [
        "Aggregation requires one currency. "
        "Provide --currency for mixed-currency ranges."
    ]
    assert aggregation_report.requests == []


def test_run_quits_cleanly_when_start_month_selection_is_cancelled() -> None:
    """Cancelling start-month selection should exit without running the aggregation."""
    presenter = RecordingPresenter()
    workflow = HistoryAggregatedBalanceReport(
        fetcher=FakeFetchService(balance_counts=[(Month(2025, 11), 5)]),
        aggregation_report=FakeAggregationReport(
            OperationResult(success=True, data=None)
        ),
        presenter=presenter,
    )

    result = workflow.run(
        start_month=None,
        end_month=Month(2025, 11),
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
    )

    assert not result.success
    assert presenter.no_start_month_selected_calls == 1


def test_run_quits_cleanly_when_end_month_selection_is_cancelled() -> None:
    """Cancelling end-month selection should exit without running the aggregation."""
    presenter = RecordingPresenter()
    workflow = HistoryAggregatedBalanceReport(
        fetcher=FakeFetchService(balance_counts=[(Month(2025, 11), 5)]),
        aggregation_report=FakeAggregationReport(
            OperationResult(success=True, data=None)
        ),
        presenter=presenter,
    )

    result = workflow.run(
        start_month=Month(2025, 9),
        end_month=None,
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
    )

    assert not result.success
    assert presenter.no_end_month_selected_calls == 1


def test_run_quits_cleanly_when_dimension_selection_is_cancelled() -> None:
    """Cancelling dimension selection should exit without running the aggregation."""
    presenter = RecordingPresenter()
    workflow = HistoryAggregatedBalanceReport(
        fetcher=FakeFetchService(),
        aggregation_report=FakeAggregationReport(
            OperationResult(success=True, data=None)
        ),
        presenter=presenter,
    )

    result = workflow.run(
        start_month=Month(2025, 9),
        end_month=Month(2025, 11),
        dimension=None,
        currency_code="USD",
    )

    assert not result.success
    assert presenter.no_dimension_selected_calls == 1


def test_run_quits_cleanly_when_currency_selection_is_cancelled() -> None:
    """Cancelling currency selection should exit without running the aggregation."""
    start_month = Month(2025, 9)
    end_month = Month(2025, 11)
    presenter = RecordingPresenter()
    workflow = HistoryAggregatedBalanceReport(
        fetcher=FakeFetchService(
            range_currencies={
                (start_month, end_month, AccountStatusScope.ACTIVE): ["CHF", "USD"]
            }
        ),
        aggregation_report=FakeAggregationReport(
            OperationResult(success=True, data=None)
        ),
        presenter=presenter,
    )

    result = workflow.run(
        start_month=start_month,
        end_month=end_month,
        dimension=AggregationDimension.CATEGORY,
        currency_code=None,
    )

    assert not result.success
    assert presenter.no_currency_selected_calls == 1
