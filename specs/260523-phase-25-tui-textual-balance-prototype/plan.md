# Plan — TUI Step 2: Textual Balance Update Prototype

## Task Groups

### 1. Dependency and entry point

1.1. Add `textual` to `pyproject.toml` dependencies and run `uv sync` to lock it.

1.2. Create `entrypoints/tui/__init__.py` and `entrypoints/tui/app.py` with a minimal
     `TextualApp` subclass that can be launched (even if blank) to confirm the dependency
     is wired correctly.

1.3. Add a `tui` command group to the Typer CLI app (e.g., `entrypoints/cli/commands/tui.py`)
     with a single `launch` subcommand that calls `app.run()`. Register it in the top-level
     CLI app.

1.4. Confirm `uv run nwtrack tui launch` starts and exits cleanly.

### 2. TUI composition root

2.1. Create `bootstrap/tui_composition.py` modelled on `bootstrap/composition.py`. Wire the
     same `SQLiteSessionManager`, `SQLAlchemyUnitOfWork`, and `FetchService` that the CLI uses.
     No presenter adapters needed yet — the Textual screen will own its own UI calls.

2.2. Verify that the TUI composition root can resolve `FetchService` and `UnitOfWork` and
     that querying the real database works from a simple Textual worker (log output or print
     to confirm).

### 3. Protocol compatibility spike

3.1. Attempt to run `BalanceUpdater.run()` in a Textual `@work` worker thread, using a
     synchronization primitive (e.g., `asyncio.Queue` or `threading.Event`) to bridge
     `prompt_for_account_id()` and `show_current_balance_and_prompt()` back to the Textual
     event loop.

3.2. Evaluate the result:
     - If workable: proceed with a thin `TextualBalanceUpdatePresenter` adapter that satisfies
       the `BalanceUpdatePresenter` Protocol and drives the screen state via `app.call_from_thread`.
     - If not workable: document the specific failure mode (deadlock, complexity, async boundary
       mismatch) and proceed with a screen-owned workflow instead (task 4 below). Record the
       finding in `requirements.md` under a new "Findings" section.

### 4. Balance update screen

4.1. Create `entrypoints/tui/screens/balance_update.py` with a Textual `Screen` subclass.

4.2. On mount, load the most recent month with balances from `FetchService` and display it
     in a header or subtitle. (Full month selection can be deferred — use the most recent
     available month for the prototype.)

4.3. Populate a `DataTable` widget with one row per active account: account name, category,
     currency, current balance for the selected month formatted as a decimal amount.

4.4. Bind the Enter key on a selected row to open an inline `Input` widget pre-filled with
     the current balance. On submission, write the new amount to the database through
     `UnitOfWork` and refresh the row.

4.5. Show a footer or status bar with the current net worth for the selected month, updated
     after each balance change.

4.6. Bind Escape or `q` to exit the screen.

### 5. Wire screen into app

5.1. Update `entrypoints/tui/app.py` to push `BalanceUpdateScreen` as the initial screen.

5.2. Confirm the full flow: launch → see account grid for most recent month → navigate rows →
     edit a balance → see updated row → see updated net worth → exit.

### 6. Verify CLI is unmodified

6.1. Run `uv run nwtrack balances update` against a real database and confirm the existing
     CLI workflow operates without change.

6.2. Run `just check` (ruff + mypy + pytest) and confirm all pass.
