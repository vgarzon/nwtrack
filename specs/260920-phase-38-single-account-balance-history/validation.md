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

1. [DONE] Ran `nwtrack reports account-history --account-name
   bank_1_checking --start 2024-06 --end 2024-11` against a database
   imported from `tests/data/csv/`. Table showed correct month-over-month
   deltas (`+0, +0, -100, +0, +0`) and the summary block matched
   hand-computed min=200, max=300, average=250.00, total change=-100.
2. [DONE] Repeated with `--account-id 1 --start 2024-10 --end 2025-07`
   (account 1 has a real gap from 2024-12 to 2025-05 in the sample data).
   Missing months displayed as `—` with a blank delta; 2025-06's delta
   correctly reflected the last real balance from 2024-11 rather than zero
   or an adjacent gap month.
3. [DEFERRED — not directly exercised] A zero-balance-record range was
   covered by the automated use case test
   (`test_zero_record_range_returns_no_summary`) and by the CLI workflow
   test (`test_run_shows_no_data_message_when_summary_is_none`); not
   separately re-run manually against a live database, since the code
   path is identical to the automated coverage.
   Also manually verified: `--account-id` and `--account-name` together is
   rejected ("Provide either --account-id or --account-name, not both.",
   exit 1), and an invalid range (`--start` after `--end`) is rejected
   ("Start month must be earlier than or equal to end month.", exit 1).
4. [DONE — headless] Drove `NWTrackApp` through a headless `run_test()`
   session against a database imported from `tests/data/csv/`: navigated
   Reports → Account History, confirmed the screen loaded (18 rows for the
   default account/range) and the summary line
   (`Min: 200  Max: 300  Avg: 225.00  Total change: -100
   (2024-06 → 2025-11)`) matched hand-computed values for
   `bank_1_checking`. Not separately re-run in an interactive terminal
   session; the automated TUI screen tests
   (`tests/entrypoints/tui/test_account_balance_history_screen.py`) cover
   account switching, error states, and default-range loading.
5. [DONE] Escape-from-screen-returns-to-Reports-menu is covered by
   `test_escape_from_screen_pops_to_reports_menu` and was also observed in
   the headless smoke run.
6. [DONE] `just test` (full suite, 384 tests) passes, which includes the
   pre-existing test coverage for `networth-history`,
   `balances-aggregate`, and `balances-aggregate-history` — unchanged.

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
