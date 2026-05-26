# Phase 31 Requirements: TUI Balance Operations

## Scope

### What this phase covers

Add two balance operation screens to the TUI, each triggered from the existing
`BalanceUpdateScreen` via keyboard bindings:

| Binding | Operation | New screen |
|---------|-----------|------------|
| `r` | Roll balances forward | `RollForwardScreen` |
| `t` | Transfer amount between accounts | `TransferScreen` |

All three operations follow the **screen-owned workflow pattern** established in Phase 25:
the screen coordinates directly with `FetchService` and `UnitOfWork` rather than driving
a CLI use-case presenter.

### What this phase does NOT cover

- New home menu items for balance operations (accessed from balance update screen only)
- Delete balance: setting a balance to zero (via the edit row flow) or deactivating an
  account covers the same intent; a standalone delete/create pair would add CRUD symmetry
  overhead without clear TUI benefit; the CLI `balances delete` command remains available
- Currency conversion for net worth display (hardcoded to USD, matching existing behavior)

---

## Decisions

### D1 — Separate screens pushed from `BalanceUpdateScreen`

Roll-forward and transfer each push a full `Screen` onto the stack. Delete reuses the
existing `ConfirmModal` (already proven for account deletion in Phase 30). Escape from
any operation screen/modal returns to `BalanceUpdateScreen`.

**Rationale**: Roll-forward and transfer have multi-step flows (month selection, account
selection, amount entry, confirmation preview) that suit a dedicated screen. Delete is
a single-step confirmation for an already-selected row, so a modal suffices.

### D2 — Roll-forward auto-computes the target month

`RollForwardScreen` computes the next free month on mount (same logic as
`RollBalancesUpdater.get_next_free_month()`). The source month defaults to the month
currently selected on `BalanceUpdateScreen` (passed as a constructor argument) but the
user can change it via a `Select` or the `MonthPickerModal`. The target month is displayed
as read-only. After success, `BalanceUpdateScreen` refreshes to show the target month.

### D3 — Transfer collects all inputs on one screen

`TransferScreen` receives the current month as a default. The screen presents:
1. Month (pre-populated, changeable via `MonthPickerModal`)
2. From-account (Select from active accounts with a balance in that month)
3. To-account (Select from active accounts, excluding the from-account)
4. Amount (Input, positive integer cents)
5. Preview panel showing computed deltas before confirmation (`Ctrl+S` to execute)

**Rationale**: Keeping all transfer inputs on one screen avoids a multi-step wizard while
remaining consistent with the "modal form" pattern used in `AccountFormModal`.

### D4 — Keyboard shortcuts on `BalanceUpdateScreen`

```
r  Roll forward
t  Transfer
```

These are additive — existing bindings (`escape`, `m`) are unchanged.

### D5 — Source/target side semantics for transfer

Reuse the `_compute_deltas` logic from `BalanceTransfer` (the existing use case). The TUI
does not duplicate this logic; it calls the same helper directly or inlines the same
formula to avoid importing CLI-layer code.

---

## Context

### Existing patterns to follow

- **Screen-owned workflow**: `BalanceUpdateScreen` calls `FetchService` and `UnitOfWork`
  directly. New screens follow the same pattern (`fetcher`, `uow` via constructor).
- **`ConfirmModal`**: already implemented in `confirm_modal.py` (Phase 30). Reuse it.
- **`MonthPickerModal`**: already implemented in `month_picker.py` (Phase 27). Reuse it.
- **`call_after_refresh`**: use for table/header refreshes after async workflows, matching
  the pattern established in Phase 30 account screens.
- **`@work` decorator**: all `async def` action handlers must use `@work`.
- **Amount formatting**: `f"{amount:,}"` — matches existing balance table display.

### Transfer delta semantics (accounting correctness)

The from-account loses economic value; the to-account gains it. Because liabilities are
stored as positive amounts, "losing value" for a liability means its stored amount increases.

| From side | To side | From delta | To delta |
|-----------|---------|------------|----------|
| ASSET     | ASSET   | −amount    | +amount  |
| ASSET     | LIABILITY | −amount  | −amount  |
| LIABILITY | ASSET   | +amount    | +amount  |
| LIABILITY | LIABILITY | +amount  | −amount  |

Missing balances for a month are treated as 0 (a new balance record is inserted).

### Roll-forward behavior

- Copies all **active** account balances from source month to target month atomically
- Target month is the first calendar month after the latest month that has any balance
- If the target month already has balances, the operation should warn and not overwrite
- After success, `BalanceUpdateScreen` navigates to the target month

### Open questions documented for future phases

- Transfer amount unit: currently integers (smallest-unit). No change needed — matches
  existing balance storage. Display and input remain in smallest units (cents for USD).
- Multi-currency transfers: not addressed in this phase; transfer operates within the
  month's stored integer amounts without conversion.
