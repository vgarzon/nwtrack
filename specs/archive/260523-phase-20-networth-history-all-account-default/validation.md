# Phase 20 Validation: Networth History All-Account Default

> **Status: complete** — 228 tests pass; ruff and mypy clean.

## Automated Tests

### `test_report_networth_history.py`

- **Default scope includes inactive accounts**: Set up a database with at least one active and
  one inactive account, both with balances in the same month range.  Run
  `NetworthHistoryReport.run()` with no explicit `status_scope` (or `AccountStatusScope.ALL`)
  and assert that the result includes the inactive account's balance in the aggregated totals.

- **`ACTIVE` scope excludes inactive accounts**: Run the same scenario with
  `status_scope=AccountStatusScope.ACTIVE` and assert that the inactive account's balance does
  not appear in the aggregated totals.

- **Existing tests**: Review and update any tests that currently assert behavior relying on
  the `ACTIVE` default.  If an existing test passes a mock that only returns active-account
  months or balances, either update the mock or document why the test scope is intentionally
  narrow.

### `test_report_balances_aggregate_history.py` / `test_report_balances_aggregate_history_rich.py`

- **Default scope is `ALL`**: Confirm that any test exercising the default `status_scope` now
  reflects `ALL` semantics.  Update stubs or mock return values if they were set up assuming
  `ACTIVE` filtering.

- **`ACTIVE` scope**: Confirm at least one test explicitly passes `AccountStatusScope.ACTIVE`
  and verifies that inactive-account data is excluded.

---

## Manual Validation

1. Start from a database that contains at least one inactive account with historical balances.

2. Run `nwtrack reports networth-history` (no flags) and confirm the output includes the
   inactive account's contribution to the net worth totals.

3. Run `nwtrack reports networth-history --status-scope active` and confirm the inactive
   account is excluded from the totals.

4. Run `nwtrack reports balances-aggregate-history` (no flags, with a month range that covers
   the inactive account's data) and confirm the inactive account appears in the output.

5. Run `nwtrack reports balances-aggregate-history --status-scope active` for the same range
   and confirm the inactive account is absent.

6. Run `nwtrack reports networth-history --help` and confirm `--status-scope` appears with
   `[default: all]`.

7. Run `nwtrack reports balances-aggregate-history --help` and confirm the `--status-scope`
   default shows `all` (was `active`).

---

## Edge Cases

- **All accounts active**: Output is identical to the previous behavior; no regression.
- **All accounts inactive**: Report still runs and includes the inactive balances; no empty-data
  error unless there are genuinely no balance records for the requested range.
- **No balance data at all**: Existing no-data warning path is exercised; behavior unchanged.

---

## Quality Checks

- `ruff check src/ tests/` passes with no errors or warnings.
- `mypy src/ tests/` passes with no errors.
- `pytest` full suite passes.

---

## Definition of Done

- `nwtrack reports networth-history` defaults to `AccountStatusScope.ALL` and accepts
  `--status-scope active|all`.
- `nwtrack reports balances-aggregate-history` defaults to `AccountStatusScope.ALL`; the
  `--status-scope` option continues to work as before.
- `NetworthHistoryReport.run()` accepts `status_scope` as an injectable parameter.
- All automated tests pass, including new tests covering both scope values on
  `networth-history`.
- `ruff`, `mypy`, and `pytest` pass.
- No other reporting commands are modified in this phase.
