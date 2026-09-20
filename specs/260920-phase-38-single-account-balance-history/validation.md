# Phase 38: Single Account Balance History Report — Validation

## Automated Tests

- Core use case tests (`tests/use_cases/test_report_account_history.py`)
  run against the real `sample_entities` fixture data rather than synthetic
  fakes: account 1 (`bank_1_checking`) already has a real gap between
  2024-11 and 2025-06 in `tests/data/csv/balances.csv`, and account 3
  (`credit_cards_1`) has different amounts either side of that same gap,
  which is enough to prove delta math skips the gap correctly. [DONE]
- `just test` (`pytest`) passes, including new coverage for:
  - **Gap handling correctness**: given balances at months M1 and M3 (M2
    missing), the report shows M2 with a blank balance, and M3's delta is
    computed as `balance(M3) - balance(M1)`, not `balance(M3) - 0` and not
    a delta against a missing M2 value.
  - **Summary stats exclude gap months**: min/max/average are computed only
    over M1 and M3's actual balances in the example above; a gap month must
    not pull average toward zero.
  - **Zero-record range**: an account with no balance records in the
    selected range returns `summary=None` and the use case reports a
    no-data outcome rather than raising or returning a fabricated summary.
  - **Single-record range**: exactly one balance record in range — no
    delta is computable for that row (`delta=None`), summary
    min=max=average=that value, `total_change=0`.
  - **Invalid range**: `start_month > end_month` returns
    `OperationResult(success=False, ...)` with a clear error message.
  - **Unknown account**: an `account_id` that doesn't exist returns a clear
    validation error, not an unhandled exception.
  - **CLI account selection**: both `--account-id` and `--account-name`
    paths resolve to the same account and produce equivalent output;
    supplying neither or both is rejected with a clear error.
- `just typecheck` (`mypy`) passes with no new `Any`/ignored-error
  suppressions introduced for this feature.
- `just lint` (`ruff`) passes.

## Manual Validation

1. Run `nwtrack reports account-history --account-name <existing account>
   --start <YYYY-MM> --end <YYYY-MM>` against a real local database with a
   full run of monthly balances for that account. Confirm the table shows
   correct month-over-month deltas and the summary block matches
   hand-computed min/max/average/total change.
2. Repeat against an account with at least one missing month in the
   selected range. Confirm the missing month displays as blank, the next
   real month's delta reflects the last real balance (not zero and not the
   immediately preceding calendar month), and the missing month is excluded
   from the summary stats.
3. Run the same report for a range with zero balance records for the
   selected account. Confirm a clear "no balance records in range" message
   is shown instead of an empty or malformed table.
4. Launch `nwtrack tui launch`, navigate Reports → Account History, select
   an account via the picker, enter a start/end month range, and confirm
   the on-screen table and summary match the CLI output for the same
   account and range.
5. From the TUI Account History screen, press Escape and confirm it returns
   to the Reports menu (not the home screen or an error).
6. Confirm existing `nwtrack reports networth-history`,
   `reports balances-aggregate`, and `reports balances-aggregate-history`
   commands are unaffected (unchanged output for a known dataset).

## Tone Check

- Report labels and error/no-data messages should match the terse, direct
  style already used in `report_presenters.py` (e.g. "No balance history
  found for <account> in <range>." rather than a verbose or apologetic
  message).

## Definition of Done

- [ ] Use case, DTOs, and repository/query support implemented and tested
- [ ] Presenter protocol + Rich CLI adapter implemented
- [ ] `nwtrack reports account-history` CLI command implemented and
      documented in `README.md` / `CLAUDE.md` command reference if such a
      reference is kept up to date elsewhere in the repo
- [ ] TUI Account History screen implemented, reachable from the Reports
      menu, and returns to the Reports menu on Escape
- [ ] All automated tests above pass; `ruff`, `mypy`, `pytest` all pass
- [ ] All manual validation steps above completed against a real local
      database
- [ ] `specs/roadmap.md` Phase 38 checkbox marked `[X]` once merged
