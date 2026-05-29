# Phase 33: TUI Status Scope Selector — Requirements

## User Problem

TUI report screens hardcode `AccountStatusScope.HISTORICAL` with no way for the user to switch
scope. Users who want to compare results under different scope filters (e.g. `active` vs
`historical`) must exit the TUI and run CLI commands manually. This phase adds an in-screen
scope selector so users can cycle between scopes without leaving the TUI.

Additional cosmetic improvements landed in this phase:
- Start/end date selections in `NetWorthHistoryScreen` are preserved when scope changes
- Amount values in `BalanceUpdateScreen` are right-justified for readability
- `NetWorthHistoryScreen` shows a per-month Delta column and a Total delta summary row

## Scope

### In scope

- Add a `Select` scope dropdown to `NetWorthHistoryScreen`
- Add the same `Select` scope dropdown to `AggregationScreen`
- Both selectors expose all three `AccountStatusScope` values: `historical`, `active`, `all`
- Both screens default to `AccountStatusScope.HISTORICAL` (consistent with CLI defaults and Phase 32)
- Changing the selected scope triggers an immediate data reload with no confirm step
- The selected scope is reflected in the screen subtitle alongside the existing month label(s)
- The `_STATUS_SCOPE` module-level constants in both screen files are replaced by instance state
  driven by the selector
- Start/end month selections in `NetWorthHistoryScreen` are pinned across scope changes
- Amount column in `BalanceUpdateScreen` DataTable is right-justified
- `NetWorthHistoryScreen` DataTable adds a `Delta` column (month-over-month net worth change)
  and a `Total` summary row at the bottom showing the net change across the selected range

### Not in scope

- Persisting scope selection across sessions or between screens
- Adding a scope selector to any other TUI screen (e.g. `BalanceUpdateScreen`, account screens)
- Changing the `AccountStatusScope` enum, the DTO layer, or any application/domain code
- CSS or visual polish beyond the baseline Textual `Select` rendering

## Widget: Textual `Select`

Use `textual.widgets.Select` with the scope options as a typed list:

```python
from textual.widgets import Select

_SCOPE_OPTIONS: list[tuple[str, AccountStatusScope]] = [
    ("Historical", AccountStatusScope.HISTORICAL),
    ("Active",     AccountStatusScope.ACTIVE),
    ("All",        AccountStatusScope.ALL),
]

Select(options=_SCOPE_OPTIONS, value=AccountStatusScope.HISTORICAL, id="scope-select")
```

Handle scope changes via `on_select_changed`, disambiguated by value type:

```python
def on_select_changed(self, event: Select.Changed) -> None:
    if isinstance(event.value, AccountStatusScope):
        self._status_scope = event.value
        self._reload_for_scope()
```

In `AggregationScreen` this handler also handles the existing dimension `Select` using the same
`isinstance` pattern — both `AggregationDimension` and `AccountStatusScope` branches live in a
single `on_select_changed` method.

## Layout

The `Select` is placed in `compose()` between the month button(s) and the error label:

```
Header
[month picker button(s)]
[Scope: Select dropdown]
[error label]
[DataTable]
Footer
```

### Wireframe: NetWorthHistoryScreen

```
┌──────────────────────────────────────────────────────────────┐
│  nwtrack — Net Worth History                                 │
│  2025-01 → 2025-12 (USD) | historical                        │
├──────────────────────────────────────────────────────────────┤
│  [Start: 2025-01]  [End: 2025-12]                            │
│  [Scope: Historical ▾]                                       │
├──────────────────────────────────────────────────────────────┤
│  Month    Assets      Liabilities   Net Worth   Delta        │
│  2025-01  120,000     40,000        80,000                   │
│  2025-02  125,000     39,000        86,000      +6,000       │
│  ...                                                         │
│  Total                                          +6,000       │
└──────────────────────────────────────────────────────────────┘
```

### Wireframe: AggregationScreen

```
┌──────────────────────────────────────────────────────────────┐
│  nwtrack — Single-Month Aggregation                          │
│  2025-12 — by Category | historical                          │
├──────────────────────────────────────────────────────────────┤
│  [Month: 2025-12]                                            │
│  [Dimension: Category ▾]                                     │
│  [Scope: Historical ▾]                                       │
├──────────────────────────────────────────────────────────────┤
│  Group       Amount                                          │
│  Savings     15,000                                          │
│  ...                                                         │
└──────────────────────────────────────────────────────────────┘
```

## Interaction Model

- On `Select.Changed` for the scope dropdown, update `self._status_scope` and call
  `_reload_for_scope()` immediately — no confirm step.
- `_reload_for_scope()` re-queries `get_available_aggregation_months()` for the new scope
  so the month picker reflects the correct months, then calls `_refresh_table()`.
- In `NetWorthHistoryScreen`, `_reload_for_scope()` preserves the user's pinned start/end
  months — it only sets defaults when `_start_month` or `_end_month` is `None`.
- The subtitle is updated to include the active scope label (e.g. `| historical`) alongside
  existing month/dimension labels.

## Delta column (NetWorthHistoryScreen only)

- A fifth `Delta` column is added to the history DataTable, right-justified.
- The first row's Delta cell is blank (no prior month to compare against).
- Subsequent rows show `net_worth[i] - net_worth[i-1]`, prefixed with `+` for gains.
- When the result set has more than one row, a `Total` row is appended showing
  `nws[-1].net_worth - nws[0].net_worth` in the Delta column; other columns are blank.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Widget | `Select` dropdown | Preferred over RadioSet by user; consistent with the existing dimension Select in AggregationScreen |
| Trigger | Immediate on `Select.Changed` | Consistent with how dimension Select already triggers refresh in AggregationScreen |
| Default | `AccountStatusScope.HISTORICAL` | Matches CLI defaults introduced in Phase 32 |
| All three values exposed | Yes | `historical / active / all` |
| Date pinning on scope change | Preserve pinned dates | Unconditional date reset on scope change was a usability regression; fix landed in same phase |
| Delta column | Inline in DataTable | Keeps all data in one scrollable view; no additional widget or label needed |
| Delta Total row | Appended to DataTable | Mathematically equivalent to `last - first`; rendered as a DataTable row with blank non-delta columns |
| Amount alignment | `Text(..., justify="right")` | Standard convention for numeric columns |

## Context and Constraints

- All screen changes are isolated to `entrypoints/tui/screens/`.
- No presenter Protocol, use case, or infrastructure code changes are needed.
- The `AccountStatusScope` enum (`application/dto.py`) already contains all three values.
- `ruff`, `mypy`, and `pytest` must pass before the phase is complete.
