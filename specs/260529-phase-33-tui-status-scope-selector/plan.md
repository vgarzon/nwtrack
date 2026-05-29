# Phase 33: TUI Status Scope Selector — Plan

## Task Groups

### [x] 1. NetWorthHistoryScreen — scope selector

1.1 Add `Select` import to `networth_history.py`; remove `RadioButton`, `RadioSet`.

1.2 Remove the module-level `_STATUS_SCOPE` constant. Add `self._status_scope:
    AccountStatusScope = AccountStatusScope.HISTORICAL` to `__init__`.

1.3 Add `_SCOPE_OPTIONS: list[tuple[str, AccountStatusScope]]` module constant.

1.4 Add `Select(options=_SCOPE_OPTIONS, value=AccountStatusScope.HISTORICAL, id="scope-select")`
    to `compose()` between the month buttons and the error label.

1.5 Add `on_select_changed` handler: `isinstance(event.value, AccountStatusScope)` branch
    updates `self._status_scope` and calls `_reload_for_scope()`.

1.6 `_reload_for_scope()` re-queries available months for the new scope and preserves the
    user's pinned `_start_month` / `_end_month` (only sets defaults when `None`).

1.7 Updated `on_mount` and `_refresh_table()` to use `self._status_scope`.

1.8 Updated `_update_buttons()` subtitle to include `| {scope.value}`.

### [x] 2. AggregationScreen — scope selector

2.1 Add `Select` import; remove `RadioButton`, `RadioSet`.

2.2 Remove module-level `_STATUS_SCOPE` constant; add `self._status_scope` instance var.

2.3 Add `_SCOPE_OPTIONS` module constant; add `Select` to `compose()` between the dimension
    Select and the error label (id=`"scope-select"`).

2.4 Extend existing `on_select_changed` with an `isinstance(event.value, AccountStatusScope)`
    branch that calls `_reload_for_scope()`. Remove `on_radio_set_changed`.

2.5 Updated `on_mount` and `_refresh_table()` to use `self._status_scope`.

2.6 Updated `_update_subtitle()` to include `| {scope.value}`.

### [x] 3. Date pinning fix (NetWorthHistoryScreen)

3.1 `_reload_for_scope()` guards the default-month assignment behind
    `if self._start_month is None or self._end_month is None:`, so user-pinned dates
    survive scope changes. Previously the method reset both months unconditionally.

### [x] 4. BalanceUpdateScreen — right-justify Amount column

4.1 Added `from rich.text import Text` import to `balance_update.py`.

4.2 Column header changed to `Text("Amount", justify="right")`.

4.3 Each cell value and the post-edit `update_cell_at` call wrapped in
    `Text(..., justify="right")`.

### [x] 5. NetWorthHistoryScreen — Delta column and Total row

5.1 Added `Text("Delta", justify="right")` as a fifth column in `on_mount`.

5.2 In `_refresh_table()`, the first row receives a blank delta cell; subsequent rows compute
    `delta = nw.net_worth - nws[i - 1].net_worth` with a `+` prefix for gains.

5.3 After the data rows, when `len(nws) > 1`, a `Total` summary row is appended with
    `nws[-1].net_worth - nws[0].net_worth` in the Delta column and blank other columns.

### [x] 6. Tests

6.1 Updated `test_networth_history_screen.py`:
    - `test_scope_selector_widget_is_present` — queries `#scope-select` as `Select`
    - `test_scope_change_to_active_updates_status_scope` — posts `Select.Changed(sel, ACTIVE)`
    - `test_scope_change_to_all_updates_status_scope` — posts `Select.Changed(sel, ALL)`
    - `test_scope_change_preserves_start_and_end_month` — pins dates, fires scope change,
      asserts months unchanged

6.2 Updated `test_aggregation_screen.py` with matching `Select`-based scope selector tests.

    340 tests pass total (up from 331).

### [x] 7. Quality gates

7.1 `just lint` — ruff passes with no errors.

7.2 `just typecheck` — mypy passes with no new errors.

7.3 `just test` — 340 tests pass.
