# Phase 29: TUI Report Screens — Requirements

## Scope

### What Is Included

Two new TUI report screens, both reachable from a new Reports sub-menu under the existing
"Reports" home menu item:

1. **Net Worth History screen** — displays aggregated balance history by side (assets vs.
   liabilities) across a user-selected month range, rendered as a scrollable DataTable.
2. **Single-Month Aggregation screen** — displays grouped balance totals for one selected month,
   grouped by a user-selected aggregation dimension (category, side, institution, currency, or tag).

Both screens follow the screen-owned workflow pattern established in Phase 25: they call
`FetchService` and the shared aggregation use cases directly from event handlers rather than
driving existing CLI use cases through presenter adapters.

### Navigation

- The home menu "Reports" item currently pushes a `StubScreen`. This phase replaces that with a
  `ReportsMenuScreen` that presents two options: "Net Worth History" and "Aggregation".
- Selecting an option pushes the corresponding report screen.
- Escape from a report screen returns to `ReportsMenuScreen`.
- Escape from `ReportsMenuScreen` returns to `HomeScreen`.

### What Is Not Included

- Multi-currency handling beyond what the existing CLI reports do: if a selected month or range
  contains mixed currencies and no `currency_code` is provided, the screen shows a clear error
  message rather than crashing. No currency selection UI is added this phase.
- Conversion-based aggregation (Phase 34).
- CSV export of report output (Phase 33).
- Account status scope selection (screens default to `AccountStatusScope.ALL` for history and
  `AccountStatusScope.ACTIVE` for single-month, matching CLI defaults).
- Account or balance administration from report screens.

---

## Decisions

### Screen-Owned Workflow Pattern

Both report screens instantiate `ReportHistoryAggregation` or `ReportSingleMonthAggregation`
directly and call `.run()` from Textual event handlers. This matches the pattern from Phase 25
and is consistent with how `BalanceUpdateScreen` calls `FetchService` and `UnitOfWork`.

### Month Selection: Reuse `MonthPickerModal`

The existing `MonthPickerModal` (Phase 27) is reused without modification:

- **Single-Month Aggregation screen**: one month picker button. `MonthPickerModal` is pushed on
  activation; the returned `Month` updates the query and re-renders the table.
- **Net Worth History screen**: two month picker buttons (Start and End). Each pushes
  `MonthPickerModal` independently. Re-rendering is triggered after either month changes.
- Both pickers are pre-populated with available months from `FetchService`.

### Net Worth History: Fixed Dimension and Currency

The net worth history screen always uses `AggregationDimension.SIDE` and `currency_code="USD"`,
matching the existing `nwtrack reports networth-history` CLI command. The screen is titled
"Net Worth History (USD)" and loads the last 12 available months by default.

### Single-Month Aggregation: Interactive Dimension Picker

The dimension picker is a `Select` widget (Textual built-in) populated with all five
`AggregationDimension` values. The query re-runs and the table re-renders whenever the selected
dimension changes.

Default dimension on mount: `AggregationDimension.CATEGORY`.

### Multi-Currency Error Handling

If the aggregation use case returns `success=False` (mixed-currency error), the report table is
replaced by a visible error label with the message from `OperationResult.error_message`. The
screen does not crash or return to the menu.

### Reports Navigation: Intermediate Menu Screen

A `ReportsMenuScreen` is added between `HomeScreen` and the two report screens. This is the same
pattern used by `HomeScreen` itself: a `ListView` with named items, pushing the target screen on
selection. The home screen's "Reports" branch is updated to push `ReportsMenuScreen` instead of
`StubScreen`.

### Available Months Source

Both screens derive available months from:

```python
fetcher.get_available_aggregation_months(
    dimension,
    currency_code=currency_code,
    status_scope=status_scope,
)
```

For the net worth history screen, `dimension=AggregationDimension.SIDE` and
`currency_code="USD"`. For the single-month screen, `dimension` follows the selected picker
value and `currency_code=None`.

---

## Context

### Patterns to Follow

| Concern | Existing reference |
|---------|--------------------|
| Screen structure | `entrypoints/tui/screens/balance_update.py` |
| Month picker integration | `entrypoints/tui/screens/balance_update.py` + `month_picker.py` |
| Home menu navigation | `entrypoints/tui/screens/home.py` |
| Reports sub-menu structure | Follow `HomeScreen` ListView pattern |
| Use case invocation | `report_history_aggregation.py`, `report_single_month_aggregation.py` |
| DTOs | `AggregationDimension`, `HistoryAggregationRequest`, `SingleMonthAggregationRequest` in `application/dto.py` |

### Dependency Injection

`ReportsMenuScreen`, `NetWorthHistoryScreen`, and `AggregationScreen` all receive `FetchService`
and `uow: Callable[[], UnitOfWork]` via constructor injection, matching the existing screen
pattern. No changes to `bootstrap/tui_composition.py` are required — the app already wires both.
`ReportHistoryAggregation` and `ReportSingleMonthAggregation` are instantiated inline inside the
screens (they have no external dependencies beyond `uow`).

### Keybindings

All screens follow the conventions from `tui-scope.md`:
- `Escape` — pop screen (back to previous)
- `q` — quit the application (only on `ReportsMenuScreen`; report screens use Escape only to pop)
- `Enter` / arrow keys — Textual defaults for ListView and Select widgets

### No New Dependencies

`Select` is a Textual built-in widget; no new packages are required.

### DataTable Layout: Net Worth History

Columns: `Month | Assets | Liabilities | Net Worth`

All amounts formatted with comma separators (e.g., `1,234,567`). No currency symbol in cells;
currency is stated in the screen title or subtitle.

### DataTable Layout: Single-Month Aggregation

Columns: `Group | Amount`

The `Group` column label changes to match the selected dimension (e.g., "Category", "Side",
"Institution", "Currency", "Tag"). Amount formatted with comma separators.
