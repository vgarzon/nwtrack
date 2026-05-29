# Phase 33: TUI Status Scope Selector — Plan

## Task Groups

### [x] 1. NetWorthHistoryScreen — scope selector

1.1 Add `RadioSet`, `RadioButton` imports to `networth_history.py`.

1.2 Remove the module-level `_STATUS_SCOPE` constant. Add `self._status_scope:
    AccountStatusScope = AccountStatusScope.HISTORICAL` to `__init__`.

1.3 Add the `RadioSet` to `compose()` between the month buttons and the error label.

1.4 Add `on_radio_set_changed` handler: maps button ID → `AccountStatusScope` via
    `_SCOPE_BUTTON_IDS`, updates `self._status_scope`, calls `_reload_for_scope()` which
    re-queries available months and refreshes the table.

1.5 Updated `on_mount` to use `self._status_scope` when calling
    `get_available_aggregation_months()`.

1.6 Updated `_refresh_table()` to pass `self._status_scope` to `HistoryAggregationRequest`.

1.7 Updated `_update_buttons()` to append `| {scope.value}` to `self.sub_title`.

### [x] 2. AggregationScreen — scope selector

2.1 Added `RadioButton`, `RadioSet` imports to `aggregation.py`.

2.2 Removed the module-level `_STATUS_SCOPE` constant. Added `self._status_scope:
    AccountStatusScope = AccountStatusScope.HISTORICAL` to `__init__`.

2.3 Added `RadioSet` to `compose()` between the dimension `Select` and the error label.

2.4 Added `on_radio_set_changed` handler and `_reload_for_scope()` helper following the same
    pattern as `NetWorthHistoryScreen`.

2.5 Updated `on_mount` to use `self._status_scope`.

2.6 Updated `_refresh_table()` to pass `self._status_scope` to `SingleMonthAggregationRequest`.

2.7 Updated `_update_subtitle()` to include `| {scope.value}`.

### [x] 3. Shared helper

3.1 `_SCOPE_BUTTON_IDS: dict[str, AccountStatusScope]` defined in each screen file (three
    lines; no shared module needed).

3.2 Used `scope.value` directly for subtitle display — already human-readable.

### [x] 4. Tests

4.1 Added 4 tests to `test_networth_history_screen.py`:
    - `test_default_status_scope_is_historical`
    - `test_scope_selector_widget_is_present`
    - `test_scope_change_to_active_updates_status_scope`
    - `test_scope_change_to_all_updates_status_scope`

4.2 Added 4 tests to `test_aggregation_screen.py` with the same coverage.

    Event simulation uses `radio_set.post_message(RadioSet.Changed(radio_set, btn))` — the
    same direct event-posting pattern used by existing TUI tests.

    339 tests pass total (up from 331).

### [x] 5. Quality gates

5.1 `just lint` — ruff passes with no errors. (Two E501 line-length issues on widget import
    lines were fixed by expanding to multi-line imports; I001 import-sort issues auto-resolved.)

5.2 `just typecheck` — mypy passes with no new errors.

5.3 `just test` — 339 tests pass.
