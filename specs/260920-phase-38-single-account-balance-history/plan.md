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

## 6. TUI Screen

6.1. Add `src/nwtrack/entrypoints/tui/screens/account_balance_history.py`:
     - Account `Select` widget (populated from `FetchService`)
     - Start/end month inputs, reusing existing month-input conventions
       from `networth_history.py` / `aggregation.py` / `month_picker.py`
     - `DataTable` for per-month rows (month, balance, delta)
     - A summary area (min/max/average/total change) below or beside the
       table
     - Resolves `AccountBalanceHistoryReport` via
       `bootstrap/tui_composition.py`
     - Escape returns to the Reports menu
6.2. Add a "Account History" entry to `reports_menu.py` that pushes the new
     screen.
6.3. Wire the use case and presenter into `bootstrap/tui_composition.py`
     (a TUI-side presenter implementation, or a lightweight adapter that
     hands data to the screen directly — follow whatever pattern
     `AggregationScreen` / `NetWorthHistoryScreen` already use for
     presenter vs. direct-data-binding).

## 7. Tests

7.1. Use case tests
     (`tests/application/use_cases/test_report_account_balance_history.py`):
     - Full contiguous range with records for every month
     - Range with one or more gap months: verify blank balance row, delta
       computed against last actual balance (not the immediately preceding
       month), and gap months excluded from summary stats
     - Range with zero balance records: summary is `None`, no-data path
     - Invalid range (`start_month > end_month`): validation error
     - Unknown `account_id`: validation error
7.2. Presenter/adapter tests (mock presenter interaction assertions,
     consistent with other report use case tests).
7.3. CLI command test (`tests/entrypoints/cli/...`) covering
     `--account-id` and `--account-name` selection paths.
7.4. TUI screen test, if the project has an existing pattern for testing
     screens (check `tests/entrypoints/tui/` for precedent before adding
     new test infrastructure).

## 8. Quality Gates

8.1. `just lint` / `ruff check` passes.
8.2. `just typecheck` / `mypy` passes.
8.3. `just test` / `pytest` passes, including new tests from Section 7.
