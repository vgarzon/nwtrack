# Phase 29: TUI Report Screens — Validation

## Automated Tests

### Test files added

- `tests/entrypoints/tui/test_reports_menu_screen.py`
- `tests/entrypoints/tui/test_networth_history_screen.py`
- `tests/entrypoints/tui/test_aggregation_screen.py`

### Test files updated

- `tests/entrypoints/tui/test_home_screen.py` — updated for Reports→ReportsMenuScreen navigation
- `tests/entrypoints/tui/test_stub_screen.py` — updated navigation to "Accounts" (2 downs)

### Results

`just check` passes: ruff, mypy, pytest all green. 287 tests pass (18 new).

---

## Definition of Done

- [x] `ReportsMenuScreen` exists and replaces the `StubScreen("Reports")` stub in `HomeScreen`
- [x] `NetWorthHistoryScreen` loads, renders a DataTable, and responds to month picker changes
- [x] `AggregationScreen` loads, renders a DataTable, and responds to month and dimension changes
- [x] Both report screens return to `ReportsMenuScreen` on Escape
- [x] `ReportsMenuScreen` returns to `HomeScreen` on Escape
- [x] Error label is shown (not a crash) for no-data cases
- [x] All three new test files pass
- [x] `just check` passes (ruff + mypy + pytest)

---

## Manual Validation Steps

Launch with a real database containing at least 3 months of data:

```bash
uv run nwtrack tui launch
```

### Reports Menu Navigation
1. Home → "Reports" (down, enter) → `ReportsMenuScreen` shown with two items
2. Escape → returns to `HomeScreen`

### Net Worth History Screen
1. Reports → "Net Worth History" (enter) → DataTable with Month/Assets/Liabilities/Net Worth columns
2. Subtitle shows date range and "(USD)"
3. Start/End buttons push `MonthPickerModal`; selecting a month updates the table
4. Escape → returns to `ReportsMenuScreen`

### Single-Month Aggregation Screen
1. Reports → "Aggregation" (down, enter) → DataTable with most recent month, Category dimension
2. Changing `Select` dimension → DataTable and subtitle update immediately
3. Month button → `MonthPickerModal`; selecting a month updates data
4. Escape → returns to `ReportsMenuScreen`

### Regression Checks
- `nwtrack reports networth-history` CLI still runs correctly
- `nwtrack tui launch` → Balance Update workflow unchanged
