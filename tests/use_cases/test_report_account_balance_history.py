"""Tests for the CLI account balance history report workflow."""

from nwtrack.application.dto import (
    AccountBalanceHistoryResult,
    AccountBalanceHistoryRow,
    AccountBalanceHistorySummary,
    OperationResult,
)
from nwtrack.application.use_cases.report_account_balance_history import (
    AccountBalanceHistoryReport,
)
from nwtrack.domain.models import Account, Status
from nwtrack.domain.value_objects import Month


class FakeFetchService:
    """Minimal fetch service double for account resolution."""

    def __init__(self, accounts: list[Account] | None = None) -> None:
        self._by_id = {a.id: a for a in (accounts or [])}
        self._by_name = {a.name: a for a in (accounts or [])}

    def get_account_by_id(self, account_id: int) -> Account | None:
        return self._by_id.get(account_id)

    def get_account_by_name(self, account_name: str) -> Account | None:
        return self._by_name.get(account_name)


class FakeHistoryReport:
    """Use-case double for the shared account balance history core query."""

    def __init__(self, result: OperationResult[AccountBalanceHistoryResult]) -> None:
        self.result = result
        self.calls: list[tuple[int, Month, Month]] = []

    def run(
        self,
        account_id: int,
        start_month: Month,
        end_month: Month,
    ) -> OperationResult[AccountBalanceHistoryResult]:
        self.calls.append((account_id, start_month, end_month))
        return self.result


class RecordingPresenter:
    """Presenter double that records account balance history interactions."""

    def __init__(self) -> None:
        self.header_calls = 0
        self.errors: list[str] = []
        self.no_data_calls: list[AccountBalanceHistoryResult] = []
        self.displayed_results: list[AccountBalanceHistoryResult] = []

    def show_header(self) -> None:
        self.header_calls += 1

    def display_account_balance_history(
        self, result: AccountBalanceHistoryResult
    ) -> None:
        self.displayed_results.append(result)

    def show_no_data_message(self, result: AccountBalanceHistoryResult) -> None:
        self.no_data_calls.append(result)

    def show_error(self, message: str) -> None:
        self.errors.append(message)


def _account(account_id: int, name: str) -> Account:
    account = Account(
        name=name,
        description="",
        category_name="checking",
        currency_code="USD",
        status=Status.ACTIVE,
    )
    account.id = account_id
    return account


def _make_result(
    start_month: Month,
    end_month: Month,
    with_summary: bool = True,
) -> AccountBalanceHistoryResult:
    row = AccountBalanceHistoryRow(month=start_month, balance=100, delta=None)
    summary = (
        AccountBalanceHistorySummary(
            min_balance=100,
            max_balance=100,
            average_balance=100.0,
            total_change=0,
            first_month=start_month,
            last_month=start_month,
        )
        if with_summary
        else None
    )
    return AccountBalanceHistoryResult(
        account_id=1,
        account_name="bank_1_checking",
        category_name="checking",
        currency_code="USD",
        institution_name=None,
        start_month=start_month,
        end_month=end_month,
        rows=[row],
        summary=summary,
    )


def test_run_resolves_account_id_and_displays_result() -> None:
    start_month = Month(2025, 1)
    end_month = Month(2025, 3)
    expected = _make_result(start_month, end_month)
    history_report = FakeHistoryReport(OperationResult(success=True, data=expected))
    presenter = RecordingPresenter()
    workflow = AccountBalanceHistoryReport(
        fetcher=FakeFetchService([_account(1, "bank_1_checking")]),
        history_report=history_report,
        presenter=presenter,
    )

    result = workflow.run(start_month=start_month, end_month=end_month, account_id=1)

    assert result.success
    assert history_report.calls == [(1, start_month, end_month)]
    assert presenter.header_calls == 1
    assert presenter.displayed_results == [expected]
    assert presenter.errors == []


def test_run_resolves_account_by_name() -> None:
    start_month = Month(2025, 1)
    end_month = Month(2025, 3)
    expected = _make_result(start_month, end_month)
    history_report = FakeHistoryReport(OperationResult(success=True, data=expected))
    presenter = RecordingPresenter()
    workflow = AccountBalanceHistoryReport(
        fetcher=FakeFetchService([_account(1, "bank_1_checking")]),
        history_report=history_report,
        presenter=presenter,
    )

    result = workflow.run(
        start_month=start_month,
        end_month=end_month,
        account_name="bank_1_checking",
    )

    assert result.success
    assert history_report.calls == [(1, start_month, end_month)]


def test_run_rejects_both_account_selectors() -> None:
    presenter = RecordingPresenter()
    workflow = AccountBalanceHistoryReport(
        fetcher=FakeFetchService([_account(1, "bank_1_checking")]),
        history_report=FakeHistoryReport(
            OperationResult(success=False, error_message="should not run")
        ),
        presenter=presenter,
    )

    result = workflow.run(
        start_month=Month(2025, 1),
        end_month=Month(2025, 3),
        account_id=1,
        account_name="bank_1_checking",
    )

    assert not result.success
    assert "not both" in result.error_message
    assert presenter.errors == [result.error_message]


def test_run_rejects_missing_account_selector() -> None:
    presenter = RecordingPresenter()
    workflow = AccountBalanceHistoryReport(
        fetcher=FakeFetchService(),
        history_report=FakeHistoryReport(
            OperationResult(success=False, error_message="should not run")
        ),
        presenter=presenter,
    )

    result = workflow.run(start_month=Month(2025, 1), end_month=Month(2025, 3))

    assert not result.success
    assert "Provide --account-id or --account-name" in result.error_message


def test_run_reports_unknown_account_name() -> None:
    presenter = RecordingPresenter()
    workflow = AccountBalanceHistoryReport(
        fetcher=FakeFetchService(),
        history_report=FakeHistoryReport(
            OperationResult(success=False, error_message="should not run")
        ),
        presenter=presenter,
    )

    result = workflow.run(
        start_month=Month(2025, 1),
        end_month=Month(2025, 3),
        account_name="does-not-exist",
    )

    assert not result.success
    assert "does-not-exist" in result.error_message


def test_run_shows_no_data_message_when_summary_is_none() -> None:
    start_month = Month(2025, 1)
    end_month = Month(2025, 3)
    expected = _make_result(start_month, end_month, with_summary=False)
    history_report = FakeHistoryReport(OperationResult(success=True, data=expected))
    presenter = RecordingPresenter()
    workflow = AccountBalanceHistoryReport(
        fetcher=FakeFetchService([_account(1, "bank_1_checking")]),
        history_report=history_report,
        presenter=presenter,
    )

    result = workflow.run(start_month=start_month, end_month=end_month, account_id=1)

    assert result.success
    assert presenter.no_data_calls == [expected]
    assert presenter.displayed_results == []


def test_run_surfaces_core_use_case_error() -> None:
    history_report = FakeHistoryReport(
        OperationResult(success=False, error_message="bad range")
    )
    presenter = RecordingPresenter()
    workflow = AccountBalanceHistoryReport(
        fetcher=FakeFetchService([_account(1, "bank_1_checking")]),
        history_report=history_report,
        presenter=presenter,
    )

    result = workflow.run(
        start_month=Month(2025, 3),
        end_month=Month(2025, 1),
        account_id=1,
    )

    assert not result.success
    assert presenter.errors == ["bad range"]
