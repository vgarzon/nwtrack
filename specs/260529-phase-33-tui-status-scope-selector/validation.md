# Phase 33: TUI Status Scope Selector — Validation

## Automated Tests

### Required assertions

**NetWorthHistoryScreen**

- Screen mounts with `_status_scope == AccountStatusScope.HISTORICAL`
- The `RadioSet` widget is present in the composed layout
- Posting a `RadioSet.Changed` event selecting `"scope-active"` causes the next
  `_refresh_table()` call to use `AccountStatusScope.ACTIVE` in the
  `HistoryAggregationRequest`
- Posting a `RadioSet.Changed` event selecting `"scope-all"` causes the next
  `_refresh_table()` call to use `AccountStatusScope.ALL`

**AggregationScreen**

- Screen mounts with `_status_scope == AccountStatusScope.HISTORICAL`
- The `RadioSet` widget is present in the composed layout
- Posting a `RadioSet.Changed` event selecting `"scope-active"` causes the next
  `_refresh_table()` call to use `AccountStatusScope.ACTIVE` in the
  `SingleMonthAggregationRequest`
- Posting a `RadioSet.Changed` event selecting `"scope-all"` causes the next
  `_refresh_table()` call to use `AccountStatusScope.ALL`

### Quality gates

```bash
just lint       # ruff — zero errors
just typecheck  # mypy — zero new errors
just test       # full pytest suite — all pass
```

## Manual Validation

### Net Worth History screen

1. `uv run nwtrack tui launch` → navigate to Reports → Net Worth History
2. Confirm the screen loads with `Historical` pre-selected in the scope RadioSet
3. Confirm the subtitle or header shows the active scope (`historical`)
4. Switch to `Active` → table reloads; verify row counts or totals differ if inactive accounts
   exist in the test database
5. Switch to `All` → table reloads; verify scope changes are reflected
6. Switch back to `Historical` → table returns to the historical view
7. Confirm month picker (Start/End buttons) still works correctly after a scope change
8. Confirm Escape returns to the Reports menu

### Aggregation screen

1. Navigate to Reports → Single-Month Aggregation
2. Confirm `Historical` is pre-selected in the scope RadioSet
3. Change dimension → table reloads (existing behaviour unchanged)
4. Switch scope to `Active` → table reloads immediately
5. Change dimension again → table reloads with the new scope still active
6. Switch scope to `All` → reloads
7. Confirm month picker still works after scope changes
8. Confirm Escape returns to the Reports menu

### Edge cases

- A database with no accounts in a given scope (e.g. no active accounts): the error label
  appears ("No data found") and the table clears; the RadioSet remains interactive so the user
  can switch back
- A database with no data at all: the initial `on_mount` error path is unchanged; the RadioSet
  is still rendered even though data is absent

## Definition of Done

- [ ] `RadioSet` scope selector is present in `NetWorthHistoryScreen` and `AggregationScreen`
- [ ] Both screens default to `AccountStatusScope.HISTORICAL`
- [ ] Selecting a different scope triggers an immediate table reload with no confirm step
- [ ] The active scope is visible in the screen subtitle
- [ ] Available months are re-queried when scope changes (so month picker reflects new scope)
- [ ] All automated tests for scope selector behaviour pass
- [ ] `just check` passes (`ruff` + `mypy` + `pytest`)
- [ ] Manual walkthrough on a real database confirms scopes produce different results where
      accounts with varying statuses exist
