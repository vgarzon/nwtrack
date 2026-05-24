# Phase 27 — TUI Month Selection and Balance Screen Polish: Requirements

## Scope

### In scope

- `MonthPickerModal`: a `ModalScreen[Month | None]` overlay for selecting the balance month
  - Shows only months that have at least one balance record in the database
  - Grid layout (3 columns), most recent month pre-selected on open
  - Arrow keys navigate the grid; Enter confirms; Escape cancels without changing the month
  - Triggered by pressing `m` from `BalanceUpdateScreen`
- `BalanceUpdateScreen` header updated to display the currently loaded month; header updates
  when the user selects a new month via the picker
- `BalanceEditModal`: a `ModalScreen[int | None]` overlay for editing a single account balance,
  replacing the current below-table `Input` widget from the Phase 25 prototype
  - Displays account name, current formatted amount, and a single `Input` field
  - Invalid amount input (non-numeric, negative, unparseable) shows an inline error label inside
    the modal; the modal does not dismiss until the user either submits a valid amount or cancels
  - Enter with valid input saves and closes; Escape cancels without saving
  - Triggered by pressing Enter on a row in the balance grid (`DataTable.RowSelected`)
- `reactive[int]` net_worth declaration removed from `BalanceUpdateScreen`; the imperative
  `_refresh_networth()` method is the sole update path (cleanup of prototype debt)
- `ruff`, `mypy`, and `pytest` pass

### Not in scope

- `HomeScreen` navigation shell and screen stack (Phase 28)
- Multi-currency / non-USD net worth handling (Phase 34)
- Textual widget snapshot tests or `App.run_test()` harness (deferred)
- Any changes to the CLI `nwtrack balances update` command or its presenter
- Balance creation for months with no existing records (the picker only shows months
  that already have balance data)

---

## Decisions

### MonthPickerModal

**Filter:** Only months with at least one balance record are shown. The list of available
months is loaded via `FetchService` (or a direct `UnitOfWork` query) when the modal mounts.
Months with no records are not shown; the user cannot navigate to an empty month from the picker.

**Layout:** 3-column grid of `YYYY-MM` strings, sorted descending (most recent top-left).
The month currently loaded in `BalanceUpdateScreen` is pre-selected on open.

**Return type:** `ModalScreen[Month | None]`. Resolves to the selected `Month` on Enter, or
`None` on Escape. `BalanceUpdateScreen` awaits the result and reloads only when the return
value is a non-`None` `Month` different from the currently loaded month.

**Keybinding on `BalanceUpdateScreen`:** `m` opens the picker. Added to `BINDINGS` with
description `"Change month"`.

### BalanceEditModal

**Replaces:** The `Input` widget displayed below the `DataTable` in the prototype. The
`Input` widget and its `display` toggling are removed from `BalanceUpdateScreen`.

**Trigger:** `DataTable.RowSelected` event on `BalanceUpdateScreen` (existing handler, now
pushes the modal instead of toggling the inline input).

**Display:** Shows the account name, month, and current balance (formatted as dollars with
two decimal places). The `Input` field starts empty; the user types the new amount.

**Amount parsing:** Accepts integers (`8500`) and decimal strings (`8500.00`). Strips leading
and trailing whitespace. Rejects empty strings, non-numeric input, and negative values.
Conversion to cents is `round(float(raw) * 100)`. If parsing fails, an error label in the
modal becomes visible with a short message (e.g. `"Enter a positive number"`); the modal
stays open.

**Return type:** `ModalScreen[int | None]`. Resolves to the new amount in cents on successful
submit, or `None` on Escape or cancel. `BalanceUpdateScreen` handles the returned int by
calling `uow.balances.update(...)` and refreshing the row and net worth label.

### reactive[int] net_worth cleanup

The `net_worth: reactive[int]` declaration on `BalanceUpdateScreen` is removed. The net worth
label is driven exclusively by `_refresh_networth()`, called after each successful balance
update and on initial screen mount. No reactive watcher is needed.

---

## Context and Implementation Notes

### Screen-owned workflow pattern

All database calls (reads and writes) happen directly in `BalanceUpdateScreen` event handlers,
not through a presenter. `FetchService` is used for read-only data loading; `UnitOfWork` is
used for balance updates. Both are injected via the constructor (established in Phase 25).

### Textual modal pattern

```python
# Pushing and awaiting a modal result
result: Month | None = await self.push_screen_wait(MonthPickerModal(current_month, available_months))
if result is not None and result != self._current_month:
    self._current_month = result
    self._reload_balances()
```

`push_screen_wait()` is the correct API for push-and-await in Textual. Do not use
`push_screen()` with a callback when the calling code needs the return value inline.

### DataTable API reminders (from tui-prototype.md)

- Enter on a focused `DataTable` fires `DataTable.RowSelected`, not a `BINDINGS` entry.
- `DataTable.update_cell_at(Coordinate(row, col), value, update_width=True)` requires
  `from textual.coordinate import Coordinate`.

### Amount display

Stored amounts are integers (cents). Display format: `$X,XXX.XX` using Python's
`f"${amount / 100:,.2f}"`. The `Input` field accepts free-form text; parsing happens in
the modal's submit handler.

### File locations

| File | Change |
|---|---|
| `entrypoints/tui/screens/balance_update.py` | Wire modals, remove inline Input, remove reactive, update header |
| `entrypoints/tui/screens/month_picker.py` | New file — `MonthPickerModal` |
| `entrypoints/tui/screens/balance_edit.py` | New file — `BalanceEditModal` |
| `entrypoints/tui/screens/__init__.py` | No change required |
