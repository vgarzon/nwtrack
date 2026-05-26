# Phase 29: TUI Report Screens — Validation

## Automated Tests

### Required test files

- `tests/entrypoints/tui/screens/test_reports_menu_screen.py`
- `tests/entrypoints/tui/screens/test_networth_history_screen.py`
- `tests/entrypoints/tui/screens/test_aggregation_screen.py`

### Assertions required

**Reports menu screen:**
- Selecting "Net Worth History" pushes a `NetWorthHistoryScreen` instance
- Selecting "Aggregation" pushes an `AggregationScreen` instance
- Constructor accepts `FetchService` and `uow` without error

**Net worth history screen:**
- On mount, `DataTable` contains at least one row when `FetchService` returns available months
- When `_refresh_table()` runs with a valid range, DataTable rows equal the number of distinct
  months in the mocked `HistoryAggregationResult`
- When the use case returns `success=False`, the error label is visible and DataTable is empty
- Changing start or end month (simulated via direct field update + `_refresh_table()`) updates
  DataTable content

**Single-month aggregation screen:**
- On mount, `_dimension` is `AggregationDimension.CATEGORY` and `_month` is the most recent
  available month from the mock fetcher
- When dimension changes, `_refresh_table()` rebuilds the DataTable with updated group labels
- When month changes, `_refresh_table()` fetches new data for the new month
- When the use case returns `success=False`, the error label is visible and DataTable is empty

### Quality gates

```bash
just check    # ruff + mypy + pytest all pass
```

No new mypy ignores. No new ruff suppressions. All new files covered by type annotations.

---

## Manual Validation

### Setup

Launch the TUI with a real database containing at least 3 months of balance data across
multiple accounts with at least 2 different categories.

```bash
uv run nwtrack tui launch
```

### Reports Menu Navigation

1. From the home menu, select "Reports" → `ReportsMenuScreen` is shown with two items.
2. Press Escape → returns to `HomeScreen`.
3. "Balances" and other home menu items still work (regression check).

### Net Worth History Screen

1. From Reports menu, select "Net Worth History".
2. Screen loads with a populated DataTable showing Month, Assets, Liabilities, Net Worth columns.
3. Subtitle shows the selected date range and "(USD)".
4. Press Escape → returns to `ReportsMenuScreen`.
5. Press the Start month button → `MonthPickerModal` appears with available months.
6. Select an earlier start month → DataTable updates to include the extended range.
7. Press the End month button → `MonthPickerModal` appears; selecting a month updates the table.
8. Set start month later than end month → error label appears; DataTable is empty.

### Single-Month Aggregation Screen

1. From Reports menu, select "Aggregation".
2. Screen loads with most recent available month and "Category" dimension selected.
3. DataTable shows one row per category with formatted amounts.
4. Change dimension via `Select` widget to "Side" → DataTable updates immediately.
5. Change dimension to "Institution" → DataTable updates with institution labels.
6. Press the Month button → `MonthPickerModal` appears; selecting a different month updates data.
7. Press Escape → returns to `ReportsMenuScreen`.

### Multi-Currency Error Case

1. If the database contains accounts in multiple currencies:
   - Set dimension to anything other than "Currency"
   - Verify error label is shown with the mixed-currency message
   - Verify screen does not crash

### Regression Check

1. `nwtrack reports networth-history` CLI command still runs correctly.
2. `nwtrack balances update` CLI command still runs correctly.
3. `nwtrack tui launch` → Balance Update workflow still works end-to-end.

---

## Definition of Done

- [ ] `ReportsMenuScreen` exists and replaces the `StubScreen("Reports")` stub in `HomeScreen`
- [ ] `NetWorthHistoryScreen` loads, renders a DataTable, and responds to month picker changes
- [ ] `AggregationScreen` loads, renders a DataTable, and responds to month and dimension changes
- [ ] Both report screens return to `ReportsMenuScreen` on Escape
- [ ] `ReportsMenuScreen` returns to `HomeScreen` on Escape
- [ ] Error label is shown (not a crash) for mixed-currency or no-data cases
- [ ] All three new test files pass
- [ ] `just check` passes (ruff + mypy + pytest)
- [ ] Manual walkthrough above completed without errors or regressions
