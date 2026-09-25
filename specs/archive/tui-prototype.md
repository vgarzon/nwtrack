# TUI Prototype — Findings and Durable Decisions

## Purpose

This document captures the architectural findings, implementation decisions, and lessons learned
from the Phase 25 TUI prototype (Textual balance update screen). Its audience is the engineer
starting Step 3 (screen model design) or Step 4 (incremental screen buildout). It is not a spec;
it is a reference for what the prototype proved and what it left open.

## What the Prototype Validated

The core claim was: **Textual can drive the balance update workflow against a real SQLite
database**. That is confirmed. `nwtrack tui launch` presents a scrollable account grid for the
most recent balance month, allows the user to select any row with arrow keys, press Enter to open
an inline edit input, submit a new amount, and see the row and net worth label update — all backed
by the real database.

The secondary claim — that the existing `BalanceUpdatePresenter` Protocol adapter-swap pattern
would work — is **not confirmed**. See the Protocol Compatibility section below.

## Protocol Compatibility Finding

**Finding: the adapter-swap pattern is not viable for interactive prompt methods.**

`BalanceUpdatePresenter.prompt_for_account_id()` and `show_current_balance_and_prompt()` are
synchronous blocking calls that assume exclusive terminal access. In a Textual application,
Textual owns the terminal; stdin is not available for arbitrary blocking reads in a worker thread.

A worker-thread approach with `threading.Event` synchronization is theoretically possible but
introduces deadlock risk, is fragile under Textual version updates, and — even if it worked —
would produce a sequential one-prompt-at-a-time experience identical to the CLI, defeating the
purpose of the TUI.

**The correct pattern for interactive Textual screens is: the screen owns the workflow.**

Display-only presenter methods (tables, headers, net worth display) could be ported to Textual
adapters cleanly. But the interactive-prompt methods need to be replaced by Textual event handlers
wired to reactive state — not wrapped in synchronization machinery.

This finding is documented in full in
`specs/260523-phase-25-tui-textual-balance-prototype/requirements.md` under "Findings".

## Implementation Pattern: Screen-Owned Workflow

The balance update screen (`entrypoints/tui/screens/balance_update.py`) calls `FetchService`
and `UnitOfWork` directly from event handlers rather than driving `BalanceUpdater.run()` through
a presenter:

```python
class BalanceUpdateScreen(Screen):
    def __init__(self, fetcher: FetchService, uow: Callable[[], UnitOfWork]) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # Open inline input for the selected row
        ...

    def on_input_submitted(self, event: Input.Submitted) -> None:
        with self._uow() as uow:
            uow.balances.update(account_id=..., month=..., new_amount=amount)
        # Refresh the row cell and net worth label
        ...
```

This pattern should be followed for all future interactive screens. Each screen receives
`FetchService` and `UnitOfWork` (or whichever services it needs) via constructor injection from
the TUI composition root.

## Textual API Notes

Lessons encountered during implementation that are not obvious from the Textual docs:

### Use `DataTable.RowSelected`, not keybindings, for Enter

`DataTable` consumes the `Enter` key internally. A `Screen`-level `BINDINGS` entry for `"enter"`
will never fire while the DataTable has focus. The correct hook is the `RowSelected` message:

```python
def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
    row_idx = event.cursor_row
    ...
```

### `Coordinate` lives in `textual.coordinate`

`DataTable.update_cell_at` requires a `Coordinate` object. It is not in `textual.geometry`:

```python
from textual.coordinate import Coordinate

table.update_cell_at(Coordinate(row, col), new_value, update_width=True)
```

### `Input` escape handling via `on_key`

To intercept Escape while an `Input` widget is displayed (to cancel editing without submitting),
handle it at the screen level in `on_key`:

```python
def on_key(self, event: Key) -> None:
    inp = self.query_one("#balance-input", Input)
    if event.key == "escape" and inp.display:
        inp.display = False
        self.query_one("#balance-table", DataTable).focus()
        event.stop()
```

### BINDINGS tuple form when not using `show=True`

Simple exit bindings can use the three-tuple form without importing `Binding`:

```python
BINDINGS = [("escape,q", "app.quit", "Quit")]
```

## TUI Composition Root Pattern

The TUI has its own composition root (`bootstrap/tui_composition.py`) that reuses
`build_base_container()` without touching the CLI composition root. Screens receive their
dependencies via the app constructor:

```python
# bootstrap/tui_composition.py
def build_tui_container() -> Container:
    container = build_base_container()
    container.register(FetchService, lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)))
    return container

# entrypoints/tui/app.py
class NWTrackApp(App):
    def __init__(self, fetcher: FetchService, uow: Callable[[], UnitOfWork]) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow

    def on_mount(self) -> None:
        self.push_screen(BalanceUpdateScreen(self._fetcher, self._uow))
```

## Files Created by the Prototype

| File | Purpose |
|------|---------|
| `pyproject.toml` | Added `textual>=3.0.0` to main dependencies |
| `bootstrap/tui_composition.py` | TUI-specific DI container |
| `entrypoints/tui/__init__.py` | Package marker |
| `entrypoints/tui/app.py` | `NWTrackApp` — top-level Textual app |
| `entrypoints/tui/screens/__init__.py` | Package marker |
| `entrypoints/tui/screens/balance_update.py` | `BalanceUpdateScreen` |
| `entrypoints/cli/commands/tui.py` | `nwtrack tui launch` CLI entry point |

## What Was Deliberately Deferred

These items are **not** present in the prototype and should be addressed in subsequent phases:

- **Month selection**: The screen always loads the most recent available month. No UI exists for
  choosing a different month. This is the most immediate gap to address in Phase 27.
- **Screen navigation**: There is no home menu or screen stack. `nwtrack tui launch` goes
  directly to the balance update screen. A navigation hierarchy is a Step 3 design question.
- **Inline cell editing**: The edit input appears below the table rather than inside the cell.
  This works but is visually disconnected. A future phase could use a modal or overlay instead.
- **Error feedback**: Invalid amount input silently closes the edit input. No error message is
  shown. Production screens should communicate parse failures to the user.
- **`reactive` field cleanup**: `net_worth: reactive[int]` is declared on the screen but not
  wired — the net worth label is updated imperatively in `_refresh_networth()`. Either wire it
  properly or remove the declaration in a cleanup pass.
- **Non-USD net worth**: The screen requests net worth in USD only. Accounts in other currencies
  are silently excluded from the total if no exchange rate exists.
- **Multi-currency accounts**: No visual indicator distinguishes USD from non-USD account rows.

## Recommended Starting Point for Phase 26

Phase 26 (TUI Screen Model Design) should answer three questions before Phase 27 implementation:

1. **Month selection UX**: How does the user navigate to a different month? Options: a modal
   picker pushed on Enter from a month header, a sidebar, or a dedicated month selection screen.
2. **Navigation model**: How does the user reach the balance update screen from a home menu?
   The `tui-scope.md` already decided on a screen stack model — Phase 26 should produce the
   screen inventory and transition diagram.
3. **Edit input UX**: Should the inline amount input stay below the table (current), appear as
   an overlay, or be rendered inside the cell? Decision informs how `BalanceUpdateScreen` is
   refactored in Phase 27.

Phase 26 deliverables should be a design document and ASCII wireframes, not code.
