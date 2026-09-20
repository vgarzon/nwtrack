# Phase 38: Single Account Balance History Report — Plan

## 1. Domain / DTO [DONE]

1.1. Add a DTO for the report result in `application/dto.py` (or a new
     module if `dto.py` is getting large — follow existing convention):
     - `AccountBalanceHistoryRow`: `month: Month`, `balance: int | None`,
       `delta: int | None` (`None` for the first row with an actual
       balance in range, since there is no prior value to diff against)
     - `AccountBalanceHistorySummary`: `min_balance: int`, `max_balance: int`,
       `average_balance: float`, `total_change: int`, `first_month: Month`,
       `last_month: Month` (the first/last months that actually have a
       balance record, for display alongside the summary)
     - `AccountBalanceHistoryResult`: account header context (`account_id`,
       `account_name`, `category_name`, `currency_code`,
       `institution_name: str | None`) + `rows: list[AccountBalanceHistoryRow]`
       + `summary: AccountBalanceHistorySummary | None` (`None` when no
       balance records exist in range)

## 2. Repository / Query [DONE — revised]

2.1. **Revised:** no new repository/SQL method was needed.
     `BalancesRepository.get_all_by_account_id(account_id)` already returns
     all balances for one account ordered by month; the use case filters
     to the requested range in Python. This avoids a bespoke SQL query for
     what is, per-account, a small dataset, consistent with "avoid raw SQL
     unless justified."
2.2. Added `FetchService.get_account_by_name()` (mirrors
     `get_account_by_id()`) for CLI `--account-name` resolution, and
     `FetchService.get_balances_for_account()` (thin wrapper over
     `get_all_by_account_id`) for the TUI screen's month-picker population.
2.3. Confirmed `account.category` and `account.institution` are already
     eager-loaded (`viewonly=True`, `lazy="selectin"`) on the `Account` ORM
     model, so header context (category name, institution name) needs no
     extra queries.

## 3. Use Case [DONE — revised]

3.1. **Revised split**, matching the existing convention where a
     presenter-free "core" use case is shared by CLI and TUI, and a
     CLI-only wrapper adds interactive/presenter concerns (see
     `report_history_aggregation.py` + `report_balances_aggregate_history.py`):
     - **Core** (implemented): `ReportAccountBalanceHistory` in
       `src/nwtrack/application/use_cases/report_account_history.py`.
       Constructor takes only `uow: Callable[[], UnitOfWork]`. `run(
       account_id, start_month, end_month) ->
       OperationResult[AccountBalanceHistoryResult]`. Builds the full month
       sequence from `start_month` to `end_month` inclusive; gap months get
       `balance=None, delta=None`; delta for a real month is computed
       against the last month that *did* have a record, not the
       immediately preceding calendar month. Summary is computed only over
       months with an actual record, and is `None` when there are zero such
       months. This is the class the TUI screen will call directly.
     - **CLI wrapper** (next): `AccountBalanceHistoryReport` in
       `report_account_balance_history.py`, taking `fetcher: FetchService`,
       `history_report` (the core use case), and a presenter; resolves
       `--account-id`/`--account-name` to one `account_id`, calls the core
       use case, and drives the presenter. Includes `main()`.
3.2. Validation implemented: reject `end_month < start_month`; reject
     unknown `account_id` with `OperationResult(success=False,
     error_message="Account {id} not found.")`.
3.3. Tests added in `tests/use_cases/test_report_account_history.py`
     against the real sample dataset (`sample_entities` fixture) rather
     than hand-built fakes, since account 1 (`bank_1_checking`) already has
     a real gap between 2024-11 and 2025-06 in the sample data — no
     synthetic fixture needed. Covers: full contiguous range, gap-month
     handling (account 3, whose amounts differ across the gap, to prove the
     delta isn't computed against zero or an adjacent gap month),
     zero-record range, single-record range, invalid range, unknown
     account, and header-context fields.

## 4. Presentation [DONE]

4.1. Added `AccountBalanceHistoryPresenter` Protocol to
     `application/ports/presentation.py`: `show_header()`,
     `display_account_balance_history(result)`, `show_no_data_message(result)`,
     `show_error(message)`.
4.2. Added `RichAccountBalanceHistoryPresenter` to
     `entrypoints/cli/adapters/report_presenters.py`, plus two renderer
     helpers in `entrypoints/cli/ui/renderers.py`:
     `build_account_balance_history_table` (month/balance/delta, blank
     balance rendered as `—`, colored `+`/`-` deltas via the existing
     `delta.negative`/`delta.positive` styles) and
     `build_account_balance_history_summary_table` (min/max/average/total
     change/range).

## 5. CLI Command [DONE]

5.1. **Revised**: added a small CLI-only wrapper use case,
     `AccountBalanceHistoryReport` in
     `report_account_balance_history.py`, that resolves
     `--account-id`/`--account-name` into one `account_id` (rejecting both
     or neither being supplied), calls the core
     `ReportAccountBalanceHistory` use case, and drives the presenter. This
     mirrors the existing core/CLI-wrapper split used by
     `report_history_aggregation.py` /
     `report_balances_aggregate_history.py`.
5.2. Added `account-history` command to
     `src/nwtrack/entrypoints/cli/commands/reports.py`:
     `nwtrack reports account-history --account-id INT | --account-name TEXT
     --start YYYY-MM --end YYYY-MM`. `--start`/`--end` are required Typer
     options (no interactive fallback, since the spec does not call for
     one); `--account-id`/`--account-name` are optional and mutually
     exclusive, enforced in the CLI wrapper use case rather than in Typer,
     so the error message is consistent between CLI and any future caller.
     Lazy import of the use case module, per existing CLI command
     convention.
5.3. Manually smoke-tested against a real SQLite DB imported from
     `tests/data/csv/`: full contiguous range, a gap range (blank rows,
     delta skips the gap), the dual-selector rejection, and the
     invalid-range rejection all produced the expected Rich output and
     exit codes.

## 6. TUI Screen [DONE — revised]

6.1. **Discovered during implementation**: TUI screens do not use the
     presenter layer at all — `NetWorthHistoryScreen` and `AggregationScreen`
     instantiate the presenter-free core use case directly
     (`ReportHistoryAggregation(uow=self._uow)`) and build their `DataTable`
     rows by hand. No changes to `bootstrap/tui_composition.py` were needed
     or made; screens only depend on `FetchService` + the `uow` factory,
     both already provided by the container.
6.2. Added `src/nwtrack/entrypoints/tui/screens/account_balance_history.py`
     (`AccountBalanceHistoryScreen`):
     - Account `Select` widget populated in `compose()` from
       `fetcher.get_accounts(active_only=False)` (all accounts, not just
       active, since balance history is meaningful for inactive accounts
       too), options as `(name, str(id))` pairs — matches the pattern in
       `transfer.py`
     - Start/end month `Button`s + `MonthPickerModal`, scoped to the
       selected account's own available months via the new
       `FetchService.get_balances_for_account()`
     - `DataTable` for per-month rows (month, balance, delta), gap months
       rendered as `—`
     - A `Label` summary line (min/max/average/total change/range) below
       the table
     - Calls `ReportAccountBalanceHistory(uow=self._uow).run(...)` directly
       — the same core use case class used by the CLI wrapper
     - Escape returns to the Reports menu (inherited `BINDINGS` pattern)
6.3. Added an "Account History" entry to `_MENU_ITEMS` in
     `reports_menu.py` and a matching `elif` branch that pushes the new
     screen.
6.4. Verified with a headless `run_test()` smoke script against a real
     SQLite database imported from `tests/data/csv/`: navigated
     Reports → Account History, confirmed 18 rows loaded for the default
     account/range and the summary line matched hand-computed values.

## 7. Tests [DONE]

7.1. Core use case tests in `tests/use_cases/test_report_account_history.py`
     (7 tests), run against real `sample_entities` data: full contiguous
     range, gap-month handling, zero-record range, single-record range,
     invalid range, unknown account, header-context fields.
7.2. CLI wrapper use case tests in
     `tests/use_cases/test_report_account_balance_history.py` (7 tests)
     using fake fetcher/history-report/presenter doubles: `--account-id`
     resolution, `--account-name` resolution, both-selectors rejection,
     neither-selector rejection, unknown-name rejection, no-data
     presenter path, core-use-case error passthrough.
7.3. `FetchService` unit tests in `tests/services/test_fetch_service.py`
     for the two new methods (`get_account_by_name`,
     `get_balances_for_account`).
7.4. CLI command registration test added to
     `tests/entrypoints/test_cli_reports.py` (`account-history` appears in
     `reports --help`).
7.5. TUI screen tests in
     `tests/entrypoints/tui/test_account_balance_history_screen.py`
     (7 tests): navigation from Reports menu, Escape back to Reports menu,
     no-accounts error, no-balances-for-account error, default range
     loads table + summary, changing the account Select reloads the
     table, `_show_error` clears the table. `test_reports_menu_screen.py`
     updated with a navigation test for the new menu entry.
7.6. No presenter/adapter-specific test file was added separately — the
     `RichAccountBalanceHistoryPresenter` is exercised indirectly via the
     manual CLI smoke tests (Section 5.3) rather than a dedicated Rich
     `Console(record=True)` unit test, consistent with the fact that its
     logic is thin formatting over already-tested `AccountBalanceHistoryResult`
     data.

## 8. Quality Gates [DONE]

8.1. `ruff check src/ tests/` — all checks passed.
8.2. `mypy src/ tests/` — no issues found (212 source files).
8.3. `pytest` — full suite passes (384 tests, includes all new tests from
     Section 7).
