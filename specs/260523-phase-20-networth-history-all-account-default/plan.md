# Phase 20 Plan: Networth History All-Account Default

> **Status: complete** — all task groups implemented and validated.

## 1. Use Case — `report_networth_history.py`

1.1 Add `status_scope: AccountStatusScope = AccountStatusScope.ALL` parameter to
    `NetworthHistoryReport.run()`.

1.2 Replace both hardcoded `AccountStatusScope.ACTIVE` references inside `run()` with the
    `status_scope` parameter:
    - `get_available_aggregation_months(...)` call
    - `HistoryAggregationRequest(...)` construction

1.3 Add `status_scope: AccountStatusScope = AccountStatusScope.ALL` parameter to `main()` and
    pass it through to `NetworthHistoryReport.run()`.

## 2. Use Case — `report_balances_aggregate_history.py`

2.1 Change the default value of `status_scope` in `HistoryAggregatedBalanceReport.run()` from
    `AccountStatusScope.ACTIVE` to `AccountStatusScope.ALL`.

2.2 Change the default value of `status_scope` in `main()` from `AccountStatusScope.ACTIVE` to
    `AccountStatusScope.ALL`.

## 3. CLI — `entrypoints/cli/commands/reports.py`

3.1 Add a `status_scope: Annotated[AccountStatusScope, typer.Option("--status-scope")]`
    parameter to `networth_history_report_interactive`, defaulting to `AccountStatusScope.ALL`.
    Pass it through to `report_networth.main(status_scope=status_scope)`.

3.2 Change the default of the existing `--status-scope` option on
    `balances_aggregate_history_report` from `AccountStatusScope.ACTIVE` to
    `AccountStatusScope.ALL`.

## 4. Tests

4.1 Review `tests/use_cases/test_report_networth_history.py`:
    - Update any assertions that assume active-only filtering now that the default is `ALL`.
    - Add a test that runs the report with a mix of active and inactive accounts and confirms
      inactive-account balances appear in the result when using the default (`ALL`) scope.
    - Add a test that passes `status_scope=AccountStatusScope.ACTIVE` and confirms
      inactive-account balances are excluded.

4.2 Review `tests/use_cases/test_report_balances_aggregate_history.py` and
    `test_report_balances_aggregate_history_rich.py`:
    - Update any assertions that assume active-only filtering as the default.
    - Confirm at least one test explicitly exercises the `ALL` path with mixed-status accounts.

## 5. Quality Gates

5.1 Run `ruff check src/ tests/` — must pass with no errors.

5.2 Run `mypy src/ tests/` — must pass with no errors.

5.3 Run `pytest` — full suite must pass.
