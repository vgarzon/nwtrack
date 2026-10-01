# Startup Balance Check — Validation

## Automated

- `just check` (ruff, mypy, pytest) passes.
- Month range helper: same month → `[]`/single as defined; across a year boundary
  (`2025-11 .. 2026-02`) yields 4 months in order.
- Repository method: copies only accounts active in the target month; an account closed in the
  target month (per `account_status_history`) is not copied; existing target rows are not
  overwritten; returns the correct row count.
- `find_gap`: empty DB → `[]`; latest == current → `[]`; latest > current → `[]`; latest =
  current-1 → one month; latest = current-3 → three months in ascending order.
- `run`: multi-month fill chains correctly (month N copied from N-1, so amounts propagate);
  an account closed mid-gap stops appearing from its closing month; a failure in any month rolls
  back every month (no partial gap in the database).
- TUI: no modal when up to date or when the DB is empty; modal text lists the missing months;
  declining leaves the balances table unchanged; approving inserts the expected rows and shows
  the follow-up prompt; accepting it pushes `BalanceUpdateScreen`.

## Manual

1. Copy a real or sample database; delete the current and previous month's balances. Launch
   `nwtrack tui launch`: modal lists both months. Approve; check balances in Reports and the
   Balances screen.
2. Repeat and decline: home screen shown normally, data unchanged; relaunch prompts again.
3. Launch with a current database: no prompt.
4. Launch with an empty database: no prompt, no error.
5. Close an account partway through the gap, then approve: it is absent from months on and
   after its closing month.
6. Cross a year boundary (latest balance month in December or earlier in the prior year).
7. Confirm a `.bak` backup is NOT created (no migration) and the log file records the fill.

## Tone check

Modal and notification copy is short, factual, and names months explicitly; no exclamation
marks; consistent with existing `ConfirmModal` messages.

## Definition of done

- All automated checks above pass and `just check` is clean.
- Manual steps 1–7 verified.
- No schema migration was needed, and `CLAUDE.md` is updated if it describes TUI startup.
- Backlog item, archive move and `CHANGELOG.md` entry done at merge time.
