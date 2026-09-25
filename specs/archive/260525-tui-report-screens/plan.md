# Phase 29: TUI Report Screens — Implementation Plan

## Status: Complete

All task groups implemented and validated. See validation.md for results.

## Task Groups

---

### [x] Group 1: Reports Menu Screen

1.1 Created `entrypoints/tui/screens/reports_menu.py` with `ReportsMenuScreen`:
   - Constructor: `(fetcher: FetchService, uow: Callable[[], UnitOfWork])`
   - `ListView` with items: "Net Worth History", "Aggregation"
   - `on_list_view_selected`: pushes `NetWorthHistoryScreen` or `AggregationScreen` with lazy imports
   - `BINDINGS`: `("escape", "app.pop_screen", "Back")`

1.2 Updated `entrypoints/tui/screens/home.py`:
   - Lazy import of `ReportsMenuScreen` inside `on_list_view_selected`
   - "Reports" item now pushes `ReportsMenuScreen` instead of `StubScreen`
   - Updated `test_home_screen.py` and `test_stub_screen.py` to match new navigation

---

### [x] Group 2: Net Worth History Screen

Created `entrypoints/tui/screens/networth_history.py` with `NetWorthHistoryScreen`:
   - Fixed `AggregationDimension.SIDE`, `currency_code="USD"`, `status_scope=AccountStatusScope.ALL`
   - On mount: loads available months, defaults to last 12, sets subtitle and populates DataTable
   - Two `Button` widgets ("Start:" / "End:") each pushing `MonthPickerModal` via `@work` handler
   - `_refresh_table()`: calls `ReportHistoryAggregation` inline, uses `to_networth_history()` adapter
   - Error label shown on no-data or failure; cleared on success

---

### [x] Group 3: Single-Month Aggregation Screen

Created `entrypoints/tui/screens/aggregation.py` with `AggregationScreen`:
   - On mount: defaults to most recent available month and `AggregationDimension.CATEGORY`
   - `Button` for month picker; `Select` widget with all five dimensions
   - `_refresh_table()`: calls `ReportSingleMonthAggregation` inline; updates column label to match dimension
   - Subtitle updated per `"{month} — by {dimension_label}"` after each refresh

---

### [x] Group 4: Wire Into App

- `app.py` and `bootstrap/tui_composition.py` required no changes
- Lazy imports used throughout reports_menu.py consistent with home.py pattern

---

### [x] Group 5: Tests

Added three new test files in `tests/entrypoints/tui/`:
- `test_reports_menu_screen.py`: navigation to both report screens, escape, subtitle
- `test_networth_history_screen.py`: navigation, escape, no-data error, `_show_error` helper
- `test_aggregation_screen.py`: navigation, escape, no-data error, default month/dimension, `_show_error` helper

Updated existing tests:
- `test_home_screen.py`: replaced "Reports→StubScreen" with "Reports→ReportsMenuScreen" assertions
- `test_stub_screen.py`: updated navigation to "Accounts" (2 downs) since "Reports" no longer stubs

All 287 tests pass. `ruff`, `mypy`, `pytest` pass.
