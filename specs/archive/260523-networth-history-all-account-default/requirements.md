# Phase 20 Requirements: Networth History All-Account Default

## User Problem

`nwtrack reports networth-history` and `nwtrack reports balances-aggregate-history` apply the
current account status to every historical month.  Accounts that were active in the past but are
now inactive or closed are silently excluded from all historical data points, producing understated
net worth figures.  Because inactive accounts should carry a zero balance, including all accounts
regardless of current status produces more accurate historical totals without requiring schema
changes.

---

## Scope

### In scope

- Change the default `status_scope` for `nwtrack reports networth-history` from
  `AccountStatusScope.ACTIVE` to `AccountStatusScope.ALL`.
- Add a `--status-scope` option to `networth-history` that accepts `active` or `all`,
  matching the pattern already used by `balances-aggregate` and `balances-aggregate-history`.
- Change the default `status_scope` for `nwtrack reports balances-aggregate-history` from
  `AccountStatusScope.ACTIVE` to `AccountStatusScope.ALL` (the option already exists; only the
  default changes).
- Thread `status_scope` through `NetworthHistoryReport.run()` and its `main()` entry point so
  it is an injectable, testable parameter instead of a hardcoded constant.

### Not in scope

- `reports balances-category`: hardcodes `ACTIVE` but is a separate compatibility command;
  deferred.
- `reports balances-aggregate` (single-month): already exposes `--status-scope`; default
  unchanged in this phase.
- Schema changes, status-history tables, or per-month effective-status logic: see Phase 25.
- Deprecation warnings or user-facing messaging when `--status-scope active` is used.

---

## Decisions

### `--status-scope active|all` over a boolean flag

`balances-aggregate` and `balances-aggregate-history` already accept `--status-scope active|all`.
Using the same option on `networth-history` keeps the CLI surface consistent and avoids a
parallel `--active-only` flag that would diverge from the established pattern.

### Default changes to `all` for both commands

The previous default (`active`) silently drops historical balances.  Changing both affected
commands to `all` by default fixes the accuracy problem without requiring any flag.  Users who
want the old behavior opt in explicitly with `--status-scope active`.

### No informational message on `--status-scope active`

The behavior is controlled by an explicit flag; no additional notice is needed.

---

## Context

- Tech stack: Python 3.12+, Typer, SQLAlchemy 2.x, Pytest, Ruff, mypy.
- `AccountStatusScope` enum (`ACTIVE`, `ALL`) and the `_apply_status_scope` infrastructure
  method already exist and handle the `ALL` case (no WHERE clause applied).
- `HistoryAggregatedBalanceReport.run()` already accepts `status_scope`; only the default and
  the CLI default need to change.
- `NetworthHistoryReport.run()` does not yet accept `status_scope`; the parameter must be
  added and the two hardcoded `AccountStatusScope.ACTIVE` references replaced.
- Follow the presenter-port pattern already in place for both use cases; no new presenter
  methods are required.
- Existing tests for both use cases should be reviewed and updated where they assert
  active-only behavior; new tests covering the `ALL` default path are required.
