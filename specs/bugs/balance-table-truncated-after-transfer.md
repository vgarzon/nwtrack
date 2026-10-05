---
name: balance-table-truncated-after-transfer
status: in-progress
severity: minor
---

## Symptom

In the TUI Balance Update screen, after the Transfer modal closes, the balances table can
render with truncated columns (e.g. `A-rathe` instead of `A-rather-long-account-name`,
`a-rather` for the category). It is intermittent. It also makes
`tests/entrypoints/tui/test_balance_operations.py::TestBalanceUpdateTableWidthAfterTransfer::test_columns_fit_content_after_transfer_modal_closes`
flaky (about 1 failure in 6–15 runs, serial or parallel).

## Repro steps

No deterministic repro yet. Loop the regression test until it fails:

```bash
for i in $(seq 1 15); do uv run pytest tests/entrypoints/tui/test_balance_operations.py::TestBalanceUpdateTableWidthAfterTransfer -q -x | tail -1; done
```

In the app: open Balance Update, press `t` to open the transfer modal, press `escape`.

## Expected vs actual

- Expected: columns fit their content after the modal closes.
- Actual: occasionally the cells are drawn at header-only widths (Account = 7, Category = 8)
  and stay that way, even after further pauses/renders.

## Version / environment

Textual 8.2.7, macOS, Python 3.12, on `devel` at `dabd2a4`.

## Suspected area

`src/nwtrack/entrypoints/tui/screens/balance_update.py` (`_refresh_table`, `action_transfer`,
deferred via `call_after_refresh`) and Textual's `DataTable` render caches.

## Diagnosis

Race inside Textual's `DataTable`:

- `_refresh_table` calls `clear(columns=True)`, `add_columns`, then `add_row` per balance. Column
  widths are only recomputed in `DataTable._on_idle`.
- If a render lands between `add_row` and that idle, cells are drawn at the stale (header-only)
  widths and cached. The cache keys of `_cell_render_cache` / `_row_render_cache` do not include
  column width, and `_update_dimensions` only clears them for auto-height rows.
- Evidence from a failing run: `Column.content_width` is correct (26/27) and `virtual_size` is
  85 wide, but `render_line` still shows `A-rathe`/`a-rather`/`asse`. Extra `pilot.pause()` calls
  do not help; calling `table._clear_caches()` and refreshing makes the full text appear.
- Commit `0d18519` deferred the refresh with `call_after_refresh` to dodge this, which narrows
  but does not close the window.

Candidate fix: after rebuilding the table, clear its caches (e.g.
`call_after_refresh(table._clear_caches)`, which uses a private Textual method) or set explicit
column widths from the content. Add a deterministic regression test that forces a render between
`add_row` and idle. Small tier: local cause, no schema change, no design decision.
