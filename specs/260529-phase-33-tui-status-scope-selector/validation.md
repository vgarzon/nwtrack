# Phase 33: TUI Status Scope Selector — Validation

## Automated Tests

### Required assertions

**NetWorthHistoryScreen** (`tests/entrypoints/tui/test_networth_history_screen.py`)

- [x] `test_default_status_scope_is_historical` — screen mounts with `_status_scope == AccountStatusScope.HISTORICAL`
- [x] `test_scope_selector_widget_is_present` — `#scope-selector` RadioSet is in the composed layout
- [x] `test_scope_change_to_active_updates_status_scope` — posting `RadioSet.Changed` for `#scope-active` sets `_status_scope` to `ACTIVE`
- [x] `test_scope_change_to_all_updates_status_scope` — posting `RadioSet.Changed` for `#scope-all` sets `_status_scope` to `ALL`

**AggregationScreen** (`tests/entrypoints/tui/test_aggregation_screen.py`)

- [x] `test_default_status_scope_is_historical` — screen mounts with `_status_scope == AccountStatusScope.HISTORICAL`
- [x] `test_scope_selector_widget_is_present` — `#scope-selector` RadioSet is in the composed layout
- [x] `test_scope_change_to_active_updates_status_scope` — posting `RadioSet.Changed` for `#scope-active` sets `_status_scope` to `ACTIVE`
- [x] `test_scope_change_to_all_updates_status_scope` — posting `RadioSet.Changed` for `#scope-all` sets `_status_scope` to `ALL`

### Quality gates

```bash
just lint       # ruff — zero errors  ✓
just typecheck  # mypy — zero new errors  ✓
just test       # 339 tests pass  ✓
```

## Manual Validation

### Net Worth History screen

1. `uv run nwtrack tui launch` → navigate to Reports → Net Worth History
2. Confirm the screen loads with `Historical` pre-selected in the scope RadioSet
3. Confirm the subtitle shows the active scope (e.g. `2025-01 → 2025-12 (USD) | historical`)
4. Switch to `Active` → table reloads immediately; verify results differ if inactive accounts exist
5. Switch to `All` → table reloads; verify scope is reflected in subtitle
6. Switch back to `Historical` → table returns to historical view
7. Confirm month picker (Start/End buttons) still works after a scope change
8. Confirm Escape returns to the Reports menu

### Aggregation screen

1. Navigate to Reports → Single-Month Aggregation
2. Confirm `Historical` is pre-selected in the scope RadioSet
3. Confirm subtitle shows scope (e.g. `2025-12 — by Category | historical`)
4. Change dimension → table reloads (existing behaviour unchanged)
5. Switch scope to `Active` → table reloads immediately
6. Change dimension again → table reloads with the new scope still active
7. Switch scope to `All` → reloads; subtitle updates
8. Confirm month picker still works after scope changes
9. Confirm Escape returns to the Reports menu

### Edge cases

- Database with no accounts matching a given scope: error label appears; RadioSet remains
  interactive so the user can switch back
- Database with no data at all: initial `on_mount` error path unchanged; RadioSet still renders

## Definition of Done

- [x] `RadioSet` scope selector present in `NetWorthHistoryScreen` and `AggregationScreen`
- [x] Both screens default to `AccountStatusScope.HISTORICAL`
- [x] Selecting a different scope triggers immediate table reload with no confirm step
- [x] Active scope visible in screen subtitle
- [x] Available months re-queried on scope change (via `_reload_for_scope()`)
- [x] All 8 scope selector tests pass; 339 total tests pass
- [x] `just check` passes (`ruff` + `mypy` + `pytest`)
- [ ] Manual walkthrough on a real database confirms scopes produce different results where
      accounts with varying statuses exist
