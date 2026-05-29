# Phase 33: TUI Status Scope Selector — Plan

## Task Groups

### 1. NetWorthHistoryScreen — scope selector

1.1 Add `RadioSet` import to `networth_history.py` alongside existing widget imports.

1.2 Remove the module-level `_STATUS_SCOPE` constant. Add `self._status_scope:
    AccountStatusScope = AccountStatusScope.HISTORICAL` to `__init__`.

1.3 Add the `RadioSet` to `compose()` between the month buttons and the error label.

1.4 Add an `on_radio_set_changed` handler (or `on_radio_set_changed` event method) that maps
    the selected button ID to `AccountStatusScope` via `_SCOPE_BUTTON_IDS`, updates
    `self._status_scope`, re-queries available months (since the available months may differ
    per scope), resets start/end month defaults, and calls `_refresh_table()`.

1.5 Update `on_mount` to use `self._status_scope` instead of the removed constant when calling
    `get_available_aggregation_months()`.

1.6 Update `_refresh_table()` to pass `self._status_scope` to `HistoryAggregationRequest` and
    to `get_available_aggregation_months()`.

1.7 Update `_update_buttons()` (or `_update_subtitle()`) to append the active scope label to
    `self.sub_title`.

### 2. AggregationScreen — scope selector

2.1 Add `RadioButton` import to `aggregation.py`; `RadioSet` is already imported (check if
    it is, otherwise add it too).

2.2 Remove the module-level `_STATUS_SCOPE` constant. Add `self._status_scope:
    AccountStatusScope = AccountStatusScope.HISTORICAL` to `__init__`.

2.3 Add the `RadioSet` to `compose()` between the dimension `Select` and the error label.

2.4 Add an `on_radio_set_changed` handler that maps the button ID to `AccountStatusScope`,
    updates `self._status_scope`, re-queries available months with the new scope, resets
    `self._month` if needed, and calls `_refresh_table()`.

2.5 Update `on_mount` to use `self._status_scope` when calling
    `get_available_aggregation_months()`.

2.6 Update `_refresh_table()` to pass `self._status_scope` to `SingleMonthAggregationRequest`.

2.7 Update `_update_subtitle()` to include the active scope label.

### 3. Shared helper

3.1 Define `_SCOPE_BUTTON_IDS: dict[str, AccountStatusScope]` in each screen file (no shared
    module needed — the dict is three lines; duplication is preferable to a premature
    extraction given these are the only two callers).

3.2 Define `_SCOPE_LABELS: dict[AccountStatusScope, str]` for subtitle display if needed, or
    use `scope.value` directly (it is already human-readable: `"historical"`, `"active"`,
    `"all"`).

### 4. Tests

4.1 Add or extend tests in `tests/entrypoints/tui/` (or the nearest existing TUI test file)
    to assert that:
    - `NetWorthHistoryScreen` initialises with `AccountStatusScope.HISTORICAL`
    - Simulating a `RadioSet.Changed` event for "active" causes the screen to query with
      `AccountStatusScope.ACTIVE`
    - `AggregationScreen` initialises with `AccountStatusScope.HISTORICAL`
    - Simulating a `RadioSet.Changed` event for "all" causes the screen to query with
      `AccountStatusScope.ALL`

4.2 Check existing TUI tests for the pattern used to drive Textual widget events in tests
    (pilot or direct event posting); follow that same pattern.

### 5. Quality gates

5.1 `just lint` — ruff passes with no errors.

5.2 `just typecheck` — mypy passes with no new errors (pay attention to the `RadioSet.Changed`
    event type; Textual types these generically — check the event attribute for the selected
    button).

5.3 `just test` — full pytest suite passes.
