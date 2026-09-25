# Phase 26 — TUI Screen Model Design: Requirements

## Scope

This is a **design-only phase**. No production code is written. The deliverables are a screen
inventory, ASCII wireframes, and explicit decisions on the three open questions from
`specs/tui-prototype.md`. These outputs unblock Phase 27 (month selection + balance screen
polish) and Phase 28 (home screen and navigation shell).

### In scope

- Screen inventory covering screens needed for Phases 27–29:
  - `HomeScreen` — top-level menu
  - `BalanceUpdateScreen` — editable monthly balance grid (already prototyped)
  - `MonthPickerModal` — month selection overlay triggered from the balance screen
  - `BalanceEditModal` — per-row amount edit overlay on the balance screen
  - `ReportsMenuScreen` — navigation hub for report workflows (Phase 28 placeholder,
    Phase 29 target)
  - `NetworthHistoryScreen` — scrollable net worth history report (Phase 29)
  - `SingleMonthAggScreen` — grouped balance report for one month (Phase 29)
- Detailed wireframes for `HomeScreen` and `BalanceUpdateScreen` (including modals)
- Sketch-level wireframes for `ReportsMenuScreen`, `NetworthHistoryScreen`,
  `SingleMonthAggScreen`
- Navigation transition diagram covering all of the above
- Three open decisions from `specs/tui-prototype.md` settled with rationale:
  1. Month selection UX
  2. Edit input UX
  3. Navigation model (confirm and document the screen stack already chosen in `tui-scope.md`)
- Keyboard navigation conventions confirmed per `tui-scope.md`

### Not in scope

- Admin CRUD screens (Phase 30: categories, institutions, tags)
- Balance roll-forward, delete, transfer screens (Phase 31)
- Import/export TUI screens (not currently phased)
- Any production code, new dependencies, or schema changes
- Automated TUI snapshot tests
- Screens for phases beyond Phase 29

---

## Decisions

### 1. Month selection UX: modal picker

**Decision:** Month selection uses a push-screen modal (`MonthPickerModal`) triggered from the
balance screen. The current month is displayed in the screen title/header; pressing `m` (or a
dedicated binding) pushes the modal. The modal presents available months, the user selects one,
and the balance screen reloads for the selected month.

**Rationale:** Month navigation is infrequent (once per monthly workflow session) but consequential
— selecting the wrong month and editing data is a meaningful error. A modal makes the action
deliberate and self-contained. It also matches the overlay pattern chosen for balance editing
(see below), keeping the interaction language consistent across the screen. An inline header
widget would save one keypress but would be visually ambiguous about what "editing the month"
means relative to "editing a balance".

**Implementation note for Phase 27:** `MonthPickerModal` should be a `ModalScreen[Month | None]`
that resolves with the selected month or `None` on cancel. The balance screen awaits the result
and reloads only on a non-`None` return.

```
┌────────────────────────────────┐
│  Select Month                  │
│                                │
│  2025-09  2025-10  2025-11     │
│  2025-12  2026-01  2026-02     │
│ ▶2026-03  2026-04              │
│                                │
│         [Cancel]  [Select]     │
└────────────────────────────────┘
  (↑↓←→ navigate, Enter selects, Escape cancels)
```

---

### 2. Edit input UX: overlay modal

**Decision:** Per-row amount editing uses a `BalanceEditModal` overlay, not the current
below-table `Input` widget. The modal shows the account name, current amount, and a single
`Input` field. Submitting saves and closes; Escape cancels without saving.

**Rationale:** The below-table input in the prototype is functional but visually disconnected from
the row being edited. An inline cell approach would require overriding `DataTable` rendering in
ways that Textual does not support cleanly. An overlay modal preserves the clean grid,
unambiguously associates the input with the selected account, allows room to show the current
amount alongside the input, and is consistent with the month picker pattern. The cost is one
extra keypress to dismiss, which is acceptable given that balance editing is a deliberate,
consequential action.

```
┌────────────────────────────────┐
│  Edit Balance                  │
│                                │
│  Account:  TFSA                │
│  Month:    2026-03             │
│  Current:  $8,300.00           │
│                                │
│  New amount: [____________]    │
│                                │
│           [Cancel]  [Save]     │
└────────────────────────────────┘
  (Enter saves, Escape cancels)
```

---

### 3. Navigation model: screen stack (confirmed)

**Decision:** `tui-scope.md` already established this — the TUI uses Textual's native screen
stack. `HomeScreen` is the entry point; selecting a workflow pushes the workflow screen; `Escape`
pops back. Phase 26 confirms this model, applies it to the near-term screen set, and documents
the full transition map.

**Navigation transition map:**

```
App launch
    │
    ▼
HomeScreen  ─── [q] ──► quit
    │
    ├── Balances ──► BalanceUpdateScreen
    │                    │
    │                    ├── [m] ──► MonthPickerModal
    │                    │              └── [Enter/Escape] ──► BalanceUpdateScreen
    │                    │
    │                    ├── [Enter on row] ──► BalanceEditModal
    │                    │                        └── [Enter/Escape] ──► BalanceUpdateScreen
    │                    │
    │                    └── [Escape] ──► HomeScreen
    │
    └── Reports ──► ReportsMenuScreen (Phase 28 placeholder → Phase 29 target)
                        │
                        ├── Net Worth History ──► NetworthHistoryScreen
                        │                            └── [Escape] ──► ReportsMenuScreen
                        │
                        └── By Dimension ──► SingleMonthAggScreen
                                                 └── [Escape] ──► ReportsMenuScreen
                        │
                        └── [Escape] ──► HomeScreen
```

---

## Screen Inventory (Phases 27–29)

| Screen | Phase | Primary Workflow | Pushed From | Pops To |
|---|---|---|---|---|
| `HomeScreen` | 28 | Top-level navigation menu | App launch | — (quit on q) |
| `BalanceUpdateScreen` | 25/27 | Edit monthly account balances | HomeScreen | HomeScreen |
| `MonthPickerModal` | 27 | Select a balance month | BalanceUpdateScreen | BalanceUpdateScreen |
| `BalanceEditModal` | 27 | Edit one account's balance | BalanceUpdateScreen | BalanceUpdateScreen |
| `ReportsMenuScreen` | 28 | Reports navigation hub | HomeScreen | HomeScreen |
| `NetworthHistoryScreen` | 29 | View net worth history table | ReportsMenuScreen | ReportsMenuScreen |
| `SingleMonthAggScreen` | 29 | View grouped balances for one month | ReportsMenuScreen | ReportsMenuScreen |

---

## Wireframes

### HomeScreen

```
┌─────────────────────────────────────────┐
│  nwtrack                        [q quit] │
├─────────────────────────────────────────┤
│                                         │
│                                         │
│    ▶  Balances                          │
│       Reports                           │
│                                         │
│                                         │
│                                         │
└─────────────────────────────────────────┘
  (↑↓ navigate, Enter pushes screen)
```

Notes:
- Accounts is excluded until Phase 30. The home menu should only list available workflows.
- Phase 28 wires Balances to `BalanceUpdateScreen` and Reports to `ReportsMenuScreen`.
- Quit is `q`; no Escape action at the home level.

---

### BalanceUpdateScreen

```
┌──────────────────────────────────────────────┐
│  ← Balances — 2026-03              [m month]  │
├──────────────────────────┬───────────────────┤
│ Account                  │ Amount            │
├──────────────────────────┼───────────────────┤
│ Checking                 │   $5,200.00       │
│ Savings                  │  $15,000.00       │
│▶TFSA                     │   $8,300.00       │
│ Credit Card              │   $2,100.00       │
│ Mortgage                 │ $240,000.00       │
├──────────────────────────┴───────────────────┤
│ Net Worth (USD):               $-203,600.00  │
└──────────────────────────────────────────────┘
  (↑↓ navigate, Enter to edit, m to change month, Escape to home)
```

Notes:
- The `← Balances` back-arrow in the title is visual only; Escape handles navigation.
- `[m month]` is a visible binding hint in the title bar.
- Net worth footer shows USD-only total (non-USD accounts excluded until Phase 34 conversion support).
- The `reactive[int]` net_worth declaration from the prototype should be removed; the label
  is updated imperatively via `_refresh_networth()` (confirmed pattern from prototype findings).

---

### MonthPickerModal (overlay on BalanceUpdateScreen)

```
        ┌────────────────────────────┐
        │  Select Month              │
        │                            │
        │  2025-09  2025-10  2025-11 │
        │  2025-12  2026-01  2026-02 │
        │ ▶2026-03  2026-04          │
        │                            │
        │       [Cancel]  [Select]   │
        └────────────────────────────┘
  (↑↓←→ navigate grid, Enter selects, Escape cancels)
```

Notes:
- Shows only months that have at least one balance record.
- The currently loaded month is pre-selected on open.
- Resolves as `ModalScreen[Month | None]`; `None` on cancel leaves the balance screen unchanged.

---

### BalanceEditModal (overlay on BalanceUpdateScreen)

```
        ┌────────────────────────────┐
        │  Edit Balance              │
        │                            │
        │  Account:  TFSA            │
        │  Month:    2026-03         │
        │  Current:  $8,300.00       │
        │                            │
        │  New amount: [__________]  │
        │                            │
        │  Error: [                ] │  ← hidden unless invalid input
        │                            │
        │       [Cancel]  [Save]     │
        └────────────────────────────┘
  (Enter saves, Escape cancels; error shown on invalid parse)
```

Notes:
- Input accepts whole-dollar amounts (e.g. `8500` or `8500.00`). Conversion to cents handled
  in the screen event handler.
- If the input cannot be parsed as a non-negative number, an error line is shown in the modal
  and the input is not dismissed. This is the fix for the prototype's silent-close behaviour.
- Resolves as `ModalScreen[int | None]`; `None` on cancel; `int` (cents) on save.

---

### ReportsMenuScreen (Phase 28 placeholder, Phase 29 target)

```
┌─────────────────────────────────────────┐
│  ← Reports                    [q quit]  │
├─────────────────────────────────────────┤
│                                         │
│    ▶  Net Worth History                 │
│       By Dimension (single month)       │
│                                         │
│                                         │
└─────────────────────────────────────────┘
  (↑↓ navigate, Enter pushes screen, Escape → Home)
```

---

### NetworthHistoryScreen (Phase 29 sketch)

```
┌─────────────────────────────────────────┐
│  ← Reports / Net Worth History [q quit] │
├──────────┬──────────┬──────────┬────────┤
│ Month    │ Assets   │ Liab     │ Net    │
├──────────┼──────────┼──────────┼────────┤
│ 2025-03  │ 120,000  │  40,000  │ 80,000 │
│ 2025-04  │ 121,500  │  39,800  │ 81,700 │
│ ...      │          │          │        │
│ [scrollable]                           │
└─────────────────────────────────────────┘
  (↑↓ scroll, Escape → Reports menu)
```

---

### SingleMonthAggScreen (Phase 29 sketch)

```
┌─────────────────────────────────────────┐
│  ← Reports / By Dimension     [q quit]  │
│  Month: 2026-03  Dimension: category    │
├──────────────────────┬──────────────────┤
│ Group                │ Total            │
├──────────────────────┼──────────────────┤
│ Cash                 │  $20,200.00      │
│ Investments          │  $65,000.00      │
│ Debt                 │ $242,100.00      │
│ ...                  │                  │
└──────────────────────┴──────────────────┘
  (↑↓ scroll, Escape → Reports menu)
```

Notes for Phase 29: month and dimension selection mechanism TBD — either pushed modals (matching
the balance screen pattern) or header-level key bindings.

---

## Keyboard Conventions (confirmed from tui-scope.md)

| Key | Action |
|---|---|
| `q` | Quit application |
| `Escape` | Back to previous screen / cancel modal |
| `↑` `↓` | Navigate list or table rows |
| `←` `→` | Navigate month grid (in MonthPickerModal) |
| `Enter` | Confirm / select / push screen |
| `Tab` / `Shift+Tab` | Next / previous focusable element |
| `m` | Open month picker (BalanceUpdateScreen only) |
| `?` | Show help (Textual default) |

No custom keybindings are introduced beyond `m` for month picker. All other navigation follows
Textual's default conventions.
