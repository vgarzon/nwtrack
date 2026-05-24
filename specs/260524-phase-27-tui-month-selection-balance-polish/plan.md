# Phase 27 — TUI Month Selection and Balance Screen Polish: Plan

## Task Group 1 — Amount Parsing Helper

These are pure functions with no Textual dependency, testable in isolation.

1.1 Write `parse_amount_input(raw: str) -> int` in a shared TUI utilities module
    (e.g. `entrypoints/tui/utils.py`). Accepts integer or decimal string, returns cents,
    raises `ValueError` on invalid input (empty, non-numeric, negative).
1.2 Write unit tests for `parse_amount_input` covering: valid integer, valid decimal,
    empty string, non-numeric string, negative value, whitespace-only.

---

## Task Group 2 — Month Picker Logic

2.1 Identify how to fetch available months from `FetchService` or a direct UoW query.
    Confirm the method returns months sorted (ascending or descending) and what type
    they are (`Month` value objects or strings).
2.2 Write a helper `months_to_grid(months: list[Month], cols: int = 3) -> list[list[Month]]`
    that arranges months into a row-major grid for display.
2.3 Write unit tests for `months_to_grid` covering: empty list, fewer months than one row,
    exact multiple of cols, non-multiple of cols.

---

## Task Group 3 — MonthPickerModal

3.1 Create `entrypoints/tui/screens/month_picker.py` with `MonthPickerModal(ModalScreen[Month | None])`.
3.2 Constructor accepts `current_month: Month` and `available_months: list[Month]`.
3.3 Compose the modal: title label, month grid (static text or Buttons in a Grid layout),
    Cancel/Select buttons or pure keybinding-driven selection.
3.4 Pre-select the cell matching `current_month` on mount.
3.5 Enter confirms the focused month and dismisses with that `Month`; Escape dismisses
    with `None`.
3.6 Arrow key navigation moves focus within the grid.

---

## Task Group 4 — BalanceEditModal

4.1 Create `entrypoints/tui/screens/balance_edit.py` with `BalanceEditModal(ModalScreen[int | None])`.
4.2 Constructor accepts `account_name: str`, `month: Month`, `current_amount_cents: int`.
4.3 Compose the modal: account/month/current-amount labels, `Input` widget, hidden error label,
    Cancel/Save buttons (or Enter/Escape keybindings).
4.4 On submit: call `parse_amount_input()`; on `ValueError` show error label and keep modal open;
    on success dismiss with the parsed cents value.
4.5 Escape dismisses with `None` at any point.

---

## Task Group 5 — BalanceUpdateScreen Wiring

5.1 Remove the inline `Input` widget and its `display` toggling from `BalanceUpdateScreen`.
5.2 Remove the `net_worth: reactive[int]` declaration; confirm `_refresh_networth()` is the
    sole update path and is called on mount and after each successful balance update.
5.3 Update the screen title/header to show `"Update Balances — {month}"` using the currently
    loaded `Month`.
5.4 Add `BINDINGS` entry `("m", "pick_month", "Change month")` and implement
    `action_pick_month()`:
    - Fetch available months
    - `await push_screen_wait(MonthPickerModal(self._current_month, available_months))`
    - On non-None result: update `self._current_month`, reload balance rows, refresh header,
      refresh net worth
5.5 Update `on_data_table_row_selected()`:
    - Remove inline Input toggling
    - `await push_screen_wait(BalanceEditModal(account_name, month, current_cents))`
    - On non-None result: write balance update via `UnitOfWork`, update cell, refresh net worth

---

## Task Group 6 — Quality Gates

6.1 Run `just check` (ruff + mypy + pytest) and fix any issues.
6.2 Confirm `reactive[int]` declaration is absent from `balance_update.py` (grep check).
6.3 Confirm `Input` display-toggling logic is absent from `balance_update.py`.
6.4 Run `nwtrack tui launch` manually and walk through the validation checklist.

---

## Notes

- Task groups 1 and 2 produce tested pure logic with no Textual dependency — implement
  and test these first before touching any screen code.
- Task groups 3 and 4 are independent and can be developed in parallel.
- Task group 5 depends on groups 3 and 4 being complete.
- Task group 6 is the final gate before the phase is considered done.
