# Phase 33: TUI Status Scope Selector — Validation

## Automated Tests

### Scope selector — NetWorthHistoryScreen (`tests/entrypoints/tui/test_networth_history_screen.py`)

- [x] `test_default_status_scope_is_historical` — screen mounts with `_status_scope == AccountStatusScope.HISTORICAL`
- [x] `test_scope_selector_widget_is_present` — `#scope-select` Select widget is in the composed layout
- [x] `test_scope_change_to_active_updates_status_scope` — posting `Select.Changed(sel, ACTIVE)` sets `_status_scope` to `ACTIVE`
- [x] `test_scope_change_to_all_updates_status_scope` — posting `Select.Changed(sel, ALL)` sets `_status_scope` to `ALL`
- [x] `test_scope_change_preserves_start_and_end_month` — pins non-default start/end, fires scope change, asserts months unchanged

### Scope selector — AggregationScreen (`tests/entrypoints/tui/test_aggregation_screen.py`)

- [x] `test_default_status_scope_is_historical` — screen mounts with `_status_scope == AccountStatusScope.HISTORICAL`
- [x] `test_scope_selector_widget_is_present` — `#scope-select` Select widget is in the composed layout
- [x] `test_scope_change_to_active_updates_status_scope` — posting `Select.Changed(sel, ACTIVE)` sets `_status_scope` to `ACTIVE`
- [x] `test_scope_change_to_all_updates_status_scope` — posting `Select.Changed(sel, ALL)` sets `_status_scope` to `ALL`

### Quality gates

```bash
just lint       # ruff — zero errors  ✓
just typecheck  # mypy — zero new errors  ✓
just test       # 340 tests pass  ✓
```

## Manual Validation

### Net Worth History screen

1. `uv run nwtrack tui launch` → navigate to Reports → Net Worth History
2. Confirm the screen loads with `Historical` pre-selected in the scope Select dropdown
3. Confirm the subtitle shows the active scope (e.g. `2025-01 → 2025-12 (USD) | historical`)
4. Confirm the DataTable has five columns: Month, Assets, Liabilities, Net Worth, Delta
5. Confirm the Delta column is blank for the first row and shows signed changes for subsequent rows
6. Confirm a Total row appears at the bottom of the table showing the net change across the range
7. Change the Start date, then switch scope → the Start and End dates are preserved
8. Switch scope to `Active` → table reloads; verify results differ if inactive accounts exist
9. Switch scope to `All` → table reloads; subtitle and Total row update
10. Confirm Escape returns to the Reports menu

### Aggregation screen

1. Navigate to Reports → Single-Month Aggregation
2. Confirm `Historical` is pre-selected in the scope Select dropdown
3. Confirm subtitle shows scope (e.g. `2025-12 — by Category | historical`)
4. Change dimension → table reloads (existing behaviour unchanged)
5. Switch scope to `Active` → table reloads immediately; subtitle updates
6. Change dimension again → table reloads with the new scope still active
7. Confirm Escape returns to the Reports menu

### Balance Update screen

1. Navigate to Balances
2. Confirm the Amount column values are right-aligned in the DataTable
3. Edit a balance → confirm the updated amount cell is also right-aligned

### Edge cases

- Database with no accounts matching a given scope: error label appears; Select dropdown
  remains interactive so the user can switch back
- Single-row result in Net Worth History: Delta and Total rows are not rendered (no prior
  month to compare against; Total only appears when `len(nws) > 1`)

## Definition of Done

- [x] `Select` scope dropdown present in `NetWorthHistoryScreen` and `AggregationScreen`
- [x] Both screens default to `AccountStatusScope.HISTORICAL`
- [x] Selecting a different scope triggers immediate table reload with no confirm step
- [x] Active scope visible in screen subtitle
- [x] Available months re-queried on scope change; pinned start/end dates preserved
- [x] Delta column and Total row in `NetWorthHistoryScreen`
- [x] Amount column right-justified in `BalanceUpdateScreen`
- [x] All 9 scope selector tests pass; 340 total tests pass
- [x] `just check` passes (`ruff` + `mypy` + `pytest`)
- [ ] Manual walkthrough on a real database confirms scopes produce different results where
      accounts with varying statuses exist
