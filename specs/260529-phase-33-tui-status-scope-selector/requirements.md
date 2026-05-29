# Phase 33: TUI Status Scope Selector — Requirements

## User Problem

TUI report screens hardcode `AccountStatusScope.HISTORICAL` with no way for the user to switch
scope. Users who want to compare results under different scope filters (e.g. `active` vs
`historical`) must exit the TUI and run CLI commands manually. This phase adds an in-screen
scope selector so users can cycle between scopes without leaving the TUI.

## Scope

### In scope

- Add a `RadioSet` scope selector to `NetWorthHistoryScreen`
- Add the same `RadioSet` scope selector to `AggregationScreen`
- Both selectors expose all three `AccountStatusScope` values: `historical`, `active`, `all`
- Both screens default to `AccountStatusScope.HISTORICAL` (consistent with CLI defaults and Phase 32)
- Changing the selected scope triggers an immediate data reload with no confirm step
- The selected scope is reflected in the screen subtitle or header alongside the existing month
  label(s)
- The `_STATUS_SCOPE` module-level constants in both screen files are replaced by instance state
  driven by the selector

### Not in scope

- Persisting scope selection across sessions or between screens
- Adding a scope selector to any other TUI screen (e.g. `BalanceUpdateScreen`, account screens)
- Changing the `AccountStatusScope` enum, the DTO layer, or any application/domain code
- CSS or visual polish beyond the baseline Textual RadioSet rendering

## Widget: Textual `RadioSet`

Use `textual.widgets.RadioSet` with three `RadioButton` children.

```python
from textual.widgets import RadioSet, RadioButton

RadioSet(
    RadioButton("Historical", id="scope-historical", value=True),
    RadioButton("Active",     id="scope-active"),
    RadioButton("All",        id="scope-all"),
    id="scope-selector",
)
```

The selected button maps to `AccountStatusScope` via a small helper:

```python
_SCOPE_BUTTON_IDS: dict[str, AccountStatusScope] = {
    "scope-historical": AccountStatusScope.HISTORICAL,
    "scope-active":     AccountStatusScope.ACTIVE,
    "scope-all":        AccountStatusScope.ALL,
}
```

## Layout

The `RadioSet` is placed in `compose()` between the month button(s) and the error label, so the
visual order from top to bottom is:

```
Header
[month picker button(s)]
[RadioSet: Historical | Active | All]
[error label]
[DataTable]
Footer
```

### Wireframe: NetWorthHistoryScreen

```
┌─────────────────────────────────────────────────────┐
│  nwtrack — Net Worth History                        │
│  2025-01 → 2025-12 (USD) | historical               │
├─────────────────────────────────────────────────────┤
│  [Start: 2025-01]  [End: 2025-12]                   │
│  Scope: ( ) Historical  ( ) Active  ( ) All         │
├─────────────────────────────────────────────────────┤
│  Month    Assets      Liabilities   Net Worth        │
│  2025-01  120,000     40,000        80,000           │
│  ...                                                │
└─────────────────────────────────────────────────────┘
```

### Wireframe: AggregationScreen

```
┌─────────────────────────────────────────────────────┐
│  nwtrack — Single-Month Aggregation                 │
│  2025-12 — by Category | historical                 │
├─────────────────────────────────────────────────────┤
│  [Month: 2025-12]                                   │
│  [Dimension: Category ▾]                            │
│  Scope: ( ) Historical  ( ) Active  ( ) All         │
├─────────────────────────────────────────────────────┤
│  Group       Amount                                 │
│  Savings     15,000                                 │
│  ...                                                │
└─────────────────────────────────────────────────────┘
```

## Interaction Model

- On `RadioSet.Changed`, read the newly selected button's ID, map it to `AccountStatusScope`,
  store it as `self._status_scope`, and call `_refresh_table()` immediately.
- No confirm step or explicit refresh trigger is required.
- The subtitle is updated to include the active scope label (e.g. `| historical`) alongside
  existing month/dimension labels.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Widget | `RadioSet` + `RadioButton` | Horizontal segmented-control feel; native Textual; already in project dependency |
| Trigger | Immediate on `RadioSet.Changed` | Consistent with how `Select.Changed` already triggers refresh in `AggregationScreen` |
| Default | `AccountStatusScope.HISTORICAL` | Matches CLI defaults introduced in Phase 32 |
| All three values exposed | Yes | User asked for `historical / active / all`; omitting any would require a rationale not yet established |
| State location | `self._status_scope` instance variable | Replaces the frozen module-level `_STATUS_SCOPE` constant; pattern mirrors `self._dimension` in `AggregationScreen` |
| CSS customisation | None | Keep default RadioSet styling; avoid coupling spec to Textual CSS version |

## Context and Constraints

- Both screens are in `entrypoints/tui/screens/`; changes are isolated to those two files.
- No presenter Protocol, use case, or infrastructure code changes are needed.
- The `AccountStatusScope` enum (`application/dto.py`) already contains all three values.
- `FetchService.get_available_aggregation_months()` already accepts `status_scope`; changing the
  scope should also re-query available months so the month picker reflects the new scope's data.
- Pattern to follow: `AggregationScreen.on_select_changed` → `_refresh_table()` is the exact
  model for wiring `RadioSet.Changed` → `_refresh_table()`.
- `ruff`, `mypy`, and `pytest` must pass before the phase is complete.
