# Phase 27 — TUI Month Selection and Balance Screen Polish: Validation

## Definition of Done

Phase 27 is complete when:

1. `MonthPickerModal` exists and is reachable from `BalanceUpdateScreen` via `m`.
2. The balance screen header displays the currently loaded month and updates after month selection.
3. `BalanceEditModal` exists and replaces the below-table `Input` from the prototype.
4. Invalid amount input shows an error in `BalanceEditModal` without dismissing the modal.
5. The `reactive[int]` net_worth declaration is absent from `BalanceUpdateScreen`.
6. Unit tests for `parse_amount_input` and `months_to_grid` pass.
7. `just check` passes (ruff + mypy + pytest).
8. Manual walkthrough below is completed without issues.

---

## Automated Quality Gates

```bash
just check   # ruff + mypy + pytest
```

### Specific test assertions required

**`parse_amount_input` (in `tests/entrypoints/tui/test_utils.py` or similar):**

| Input | Expected outcome |
|---|---|
| `"8500"` | `850000` (cents) |
| `"8500.00"` | `850000` (cents) |
| `"8500.5"` | `850050` (cents) |
| `"  1000  "` | `100000` (whitespace stripped) |
| `""` | `ValueError` |
| `"abc"` | `ValueError` |
| `"-500"` | `ValueError` |
| `"0"` | `0` (zero balance is valid) |

**`months_to_grid`:**

| Input | Expected outcome |
|---|---|
| `[]` | `[]` |
| 2 months, cols=3 | One row with 2 entries |
| 3 months, cols=3 | One row with 3 entries |
| 4 months, cols=3 | Two rows: [3, 1] |
| 6 months, cols=3 | Two rows of 3 |

### Grep checks (confirm prototype debt is removed)

```bash
# reactive[int] declaration must be gone
grep -n "reactive\[int\]" src/nwtrack/entrypoints/tui/screens/balance_update.py
# should produce no output

# Inline Input display toggling must be gone
grep -n "inp.display" src/nwtrack/entrypoints/tui/screens/balance_update.py
# should produce no output
```

---

## Manual Walkthrough

### Setup

```bash
uv run nwtrack tui launch
```

Assumes a database with at least two months of balance records for the manual steps below.

### 1. Screen loads correctly

- [ ] Balance screen opens showing the most recent available month in the header
      (e.g. `Update Balances — 2026-03`)
- [ ] Account grid is populated with account names and formatted amounts
- [ ] Net worth footer shows the USD total for the loaded month
- [ ] No below-table `Input` widget visible on initial load

### 2. Month picker — happy path

- [ ] Press `m` → `MonthPickerModal` opens as an overlay
- [ ] Modal title is visible (e.g. `"Select Month"`)
- [ ] Available months appear in a 3-column grid; the currently loaded month is pre-selected
- [ ] Arrow keys move focus to adjacent months in the grid
- [ ] Press Enter on a different month → modal closes, balance screen reloads for that month
- [ ] Screen header updates to show the newly selected month
- [ ] Net worth footer updates to reflect the new month's data

### 3. Month picker — cancel

- [ ] Press `m` → modal opens
- [ ] Press Escape → modal closes without changing the loaded month
- [ ] Screen header still shows the original month

### 4. Balance edit — happy path

- [ ] Navigate to a row with arrow keys; press Enter → `BalanceEditModal` opens as an overlay
- [ ] Modal shows account name, month, and current balance amount
- [ ] Type a new valid amount (integer or decimal)
- [ ] Press Enter → modal closes, grid row updates with the new amount, net worth footer updates
- [ ] Verify the updated value persists: press `m`, select the same month, confirm the value

### 5. Balance edit — invalid input

- [ ] Open edit modal on any row
- [ ] Type `abc` and press Enter → error label appears inside the modal (e.g. `"Enter a positive number"`)
- [ ] Modal stays open (does not dismiss)
- [ ] Clear the input, type a negative number (e.g. `-500`) and press Enter → same error behaviour
- [ ] Type a valid amount and press Enter → modal closes successfully

### 6. Balance edit — cancel

- [ ] Open edit modal on any row
- [ ] Press Escape → modal closes without saving; original amount still shown in grid

### 7. Existing CLI unaffected

```bash
uv run nwtrack balances update
```

- [ ] CLI balance update workflow functions normally (no regressions from TUI changes)

---

## Regression Risk

- The below-table `Input` removal changes the event-handling flow in `BalanceUpdateScreen`. If
  any event handler still references the removed widget by ID, the screen will raise a
  `NoMatches` error on row selection. Test by pressing Enter on multiple rows.
- `push_screen_wait()` is async; any call site that uses `push_screen()` instead will not
  receive the modal return value. Confirm with mypy that return types are handled.
- `FetchService` month-fetching must return `Month` value objects (not raw strings) for the
  month picker pre-selection comparison to work. Verify the type returned by the fetch method
  used.
