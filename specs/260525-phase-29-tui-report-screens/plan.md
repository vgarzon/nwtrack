# Phase 29: TUI Report Screens — Implementation Plan

## Task Groups

Each group is independently implementable after its predecessors are done.

---

### Group 1: Reports Menu Screen

1.1 Create `entrypoints/tui/screens/reports_menu.py` with a `ReportsMenuScreen`:
   - Constructor: `(fetcher: FetchService, uow: Callable[[], UnitOfWork])`
   - `ListView` with items: "Net Worth History", "Aggregation"
   - `on_list_view_selected`: push `NetWorthHistoryScreen` or `AggregationScreen` with injected deps
   - `BINDINGS`: `("escape", "app.pop_screen", "Back")`

1.2 Update `entrypoints/tui/screens/home.py`:
   - Import `ReportsMenuScreen` lazily inside the `on_list_view_selected` handler
   - Replace the `StubScreen("Reports")` push with `ReportsMenuScreen(self._fetcher, self._uow)`

---

### Group 2: Net Worth History Screen

2.1 Create `entrypoints/tui/screens/networth_history.py` with a `NetWorthHistoryScreen`:
   - Constructor: `(fetcher: FetchService, uow: Callable[[], UnitOfWork])`
   - Fixed dimension: `AggregationDimension.SIDE`, `currency_code="USD"`, `status_scope=AccountStatusScope.ALL`
   - `BINDINGS`: `("escape", "app.pop_screen", "Back")`

2.2 On mount:
   - Load available months via `fetcher.get_available_aggregation_months(AggregationDimension.SIDE, currency_code="USD", status_scope=AccountStatusScope.ALL)`
   - Select `start_month = available_months[-12]` (or first if fewer than 12), `end_month = available_months[-1]`
   - Set screen subtitle to reflect the range (e.g., `"2024-06 → 2025-05 (USD)"`)
   - Populate the DataTable

2.3 UI layout:
   - `Header()` + `Footer()`
   - Two `Button` widgets: "Start: YYYY-MM" and "End: YYYY-MM" — each pushes `MonthPickerModal`
   - `DataTable` with columns: Month, Assets, Liabilities, Net Worth
   - Error `Label` (hidden by default) for multi-currency or no-data cases

2.4 Month picker integration:
   - Each button's `on_button_pressed` calls `app.push_screen(MonthPickerModal(...), callback)`
   - Callback updates the corresponding month field and calls `_refresh_table()`

2.5 `_refresh_table()`:
   - Build `HistoryAggregationRequest(start_month, end_month, AggregationDimension.SIDE, currency_code="USD", status_scope=AccountStatusScope.ALL)`
   - Instantiate `ReportHistoryAggregation(uow=self._uow)` and call `.run(request)`
   - On success: clear and repopulate DataTable rows from `result.data.rows`; hide error label
   - On failure: show error label with `result.error_message`; clear DataTable

2.6 DataTable rendering:
   - Group rows by month, summing assets and liabilities from `HistoryAggregationRow` entries
     (use `row.label` to distinguish "asset" vs "liability" sides)
   - Compute net worth per month: assets − liabilities
   - Format all amounts with `f"{amount:,}"`

---

### Group 3: Single-Month Aggregation Screen

3.1 Create `entrypoints/tui/screens/aggregation.py` with an `AggregationScreen`:
   - Constructor: `(fetcher: FetchService, uow: Callable[[], UnitOfWork])`
   - Mutable state: `_month: Month`, `_dimension: AggregationDimension`
   - `BINDINGS`: `("escape", "app.pop_screen", "Back")`

3.2 On mount:
   - Load available months via `fetcher.get_available_aggregation_months(AggregationDimension.CATEGORY)`
   - Set `_month = available_months[-1]` (most recent)
   - Set `_dimension = AggregationDimension.CATEGORY`
   - Set screen subtitle to `"{month} — by {dimension}"`
   - Populate DataTable

3.3 UI layout:
   - `Header()` + `Footer()`
   - `Button` "Month: YYYY-MM" — pushes `MonthPickerModal`
   - `Select` widget populated with `AggregationDimension` values, default `CATEGORY`
   - `DataTable` with two columns: Group, Amount
   - Error `Label` (hidden by default)

3.4 Month picker integration:
   - Button press pushes `MonthPickerModal`; callback updates `_month` and calls `_refresh_table()`

3.5 Dimension picker integration:
   - `on_select_changed` updates `_dimension` and calls `_refresh_table()`

3.6 `_refresh_table()`:
   - Build `SingleMonthAggregationRequest(month=self._month, dimension=self._dimension, currency_code=None, status_scope=AccountStatusScope.ACTIVE)`
   - Instantiate `ReportSingleMonthAggregation(uow=self._uow)` and call `.run(request)`
   - On success: clear and repopulate DataTable; update subtitle; hide error label
   - On failure: show error label; clear DataTable
   - Update `Group` column label to match dimension name (e.g., "Category", "Institution")

---

### Group 4: Wire Into App

4.1 Update `entrypoints/tui/screens/reports_menu.py` imports to use lazy imports for
   `NetWorthHistoryScreen` and `AggregationScreen` (same pattern as `HomeScreen`).

4.2 Verify `entrypoints/tui/app.py` — no changes needed (home screen already receives deps).

4.3 Confirm `bootstrap/tui_composition.py` — no changes needed.

---

### Group 5: Tests

5.1 Add `tests/entrypoints/tui/screens/test_networth_history_screen.py`:
   - Test on-mount loads data and populates DataTable (use mock `FetchService` and `UnitOfWork`)
   - Test `_refresh_table()` clears and repopulates on new month selection
   - Test error label is shown when use case returns `success=False`

5.2 Add `tests/entrypoints/tui/screens/test_aggregation_screen.py`:
   - Test on-mount defaults to most recent month and `CATEGORY` dimension
   - Test dimension change triggers `_refresh_table()`
   - Test month change triggers `_refresh_table()`
   - Test error label is shown on mixed-currency failure

5.3 Add `tests/entrypoints/tui/screens/test_reports_menu_screen.py`:
   - Test that "Net Worth History" selection pushes `NetWorthHistoryScreen`
   - Test that "Aggregation" selection pushes `AggregationScreen`

5.4 Check for existing TUI screen tests and follow their fixture and mock patterns.
