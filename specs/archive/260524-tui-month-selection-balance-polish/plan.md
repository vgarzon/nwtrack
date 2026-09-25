# Phase 27 — TUI Month Selection and Balance Screen Polish: Plan

## [X] Task Group 1 — Amount Parsing Helper

1.1 `parse_amount_input(raw: str) -> int` implemented in `entrypoints/tui/utils.py`.
1.2 Unit tests in `tests/entrypoints/test_tui_utils.py` — 9 cases, all passing.

---

## [X] Task Group 2 — Month Picker Logic

2.1 `FetchService.get_recent_months()` confirmed as the source — returns `list[Month]`
    descending. Default `n_months=12`; pass a large value or use `get_balance_count_per_month()`
    directly to get all available months.
2.2 `months_to_grid(months, cols=3)` implemented in `entrypoints/tui/utils.py`.
2.3 Unit tests in `tests/entrypoints/test_tui_utils.py` — 5 cases, all passing.

---

## [X] Task Group 3 — MonthPickerModal

3.1–3.6 `MonthPickerModal(ModalScreen[Month | None])` implemented in
    `entrypoints/tui/screens/month_picker.py`. Button grid via Textual `Grid`, 3 columns.
    Pre-selects current month on mount. `Binding("escape", "cancel")` dismisses with `None`.
    Button press parses the month from the button ID and dismisses with the `Month`.

---

## [X] Task Group 4 — BalanceEditModal

4.1–4.5 `BalanceEditModal(ModalScreen[int | None])` implemented in
    `entrypoints/tui/screens/balance_edit.py`. Shows account name, month, current amount,
    and an `Input` field. `on_input_submitted` calls `parse_amount_input()`; on `ValueError`
    sets error label text and returns without dismissing. Escape cancels via action.

---

## [X] Task Group 5 — BalanceUpdateScreen Wiring

5.1 Inline `Input` widget and `on_key`/`on_input_submitted` handlers removed.
5.2 `net_worth: reactive[int]` declaration removed; `_refresh_networth()` is sole update path.
5.3 `self.sub_title` set to `"Update Balances — {month}"` in `_update_header()`.
5.4 `Binding("m", "pick_month", "Change month")` added; `action_pick_month()` implemented
    with `push_screen_wait(MonthPickerModal(...))`.
5.5 `on_data_table_row_selected` now `async`; uses `push_screen_wait(BalanceEditModal(...))`.

---

## [X] Task Group 6 — Quality Gates

6.1 `just check` passes — 262 tests, ruff clean, mypy clean.
6.2 `reactive[int]` declaration absent from `balance_update.py` (grep confirmed).
6.3 `inp.display` toggling absent from `balance_update.py` (grep confirmed).
6.4 Manual walkthrough pending (see validation.md).

---

## Notes

- Task groups 1 and 2 produce tested pure logic with no Textual dependency — implement
  and test these first before touching any screen code.
- Task groups 3 and 4 are independent and can be developed in parallel.
- Task group 5 depends on groups 3 and 4 being complete.
- Task group 6 is the final gate before the phase is considered done.
