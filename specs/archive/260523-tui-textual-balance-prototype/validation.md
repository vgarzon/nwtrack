# Validation — TUI Step 2: Textual Balance Update Prototype

## Automated checks

- `ruff check src/ tests/` passes with no errors
- `mypy src/ tests/` passes with no type errors (Textual ships type stubs; no `# type: ignore`
  shortcuts allowed for the core screen and composition code)
- `pytest` passes — existing test suite must not regress; no new tests are required for this
  phase (UI is validated manually)

## Manual walkthrough

### Setup

1. Run `uv sync` and confirm `textual` is present in the lock file.
2. Set `NWTRACK_DB_FILE_PATH` to a database with at least one month of balance data.

### TUI launch

3. Run `uv run nwtrack tui launch`.
4. Confirm the Textual application starts and displays the balance update screen for the most
   recent month with balance data.
5. Confirm the screen header or subtitle identifies the month being edited.

### Grid navigation

6. Confirm all active accounts appear as rows in the DataTable.
7. Use arrow keys to navigate between rows; confirm the cursor moves correctly.
8. Confirm account name, category (or currency), and current balance are visible per row.

### Balance editing

9. Move the cursor to any account row and press Enter.
10. Confirm an input widget appears pre-filled with the current balance.
11. Change the value and press Enter to confirm.
12. Confirm the row updates to the new balance without requiring a full screen reload.
13. Confirm the updated value is persisted — exit the TUI, then re-launch and verify the
    new balance is shown.

### Net worth update

14. After editing a balance, confirm the net worth display (footer or status bar) reflects
    the updated total.

### Exit

15. Press Escape or `q` and confirm the TUI exits cleanly with no errors or tracebacks.

### CLI preservation

16. Run `uv run nwtrack balances update` (existing CLI command) against the same database.
17. Confirm the CLI workflow operates normally end-to-end — month selection, account loop,
    balance entry, final summary.
18. Confirm the CLI and TUI agree on the stored balance values.

## Protocol compatibility finding

19. Document the outcome of the Protocol compatibility spike (plan task 3) in
    `requirements.md` under a "Findings" section:
    - State whether `BalanceUpdater.run()` was successfully driven from a Textual worker
    - If yes: describe the synchronization mechanism used and any constraints it imposes
    - If no: describe the failure mode and state what changes to the Protocol or use case
      structure would be needed to support a true adapter-swap in the full buildout phase

This finding is a required deliverable for this phase. It informs Step 3 (screen model design)
and any Protocol changes that Step 4 may need.

## Definition of done

- `uv run nwtrack tui launch` displays the balance update screen, allows editing account
  balances, and persists changes to the real database
- `uv run nwtrack balances update` still works without modification
- `just check` passes (ruff + mypy + pytest)
- The Protocol compatibility finding is documented in `requirements.md`
