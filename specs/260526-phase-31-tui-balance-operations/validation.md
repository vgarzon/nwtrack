# Phase 31 Validation: TUI Balance Operations

## Automated Tests

### Quality gates (must pass before merge)

```bash
just check   # ruff + mypy + pytest
```

### Feature-specific test assertions

**Roll-forward screen**
- `RollForwardScreen` mounts and computes the correct target month (next month after latest)
- Source and target months are displayed in the screen header or body
- Confirming executes `uow.balances.copy_by_month(source_month, target_month)`
- On success, `BalanceUpdateScreen` updates `self._month` to the target month and refreshes
- If the target month already has balances, the confirm action is disabled and an error/warning is shown
- Cancelling (Escape) does not write any data

**Transfer screen**
- From-account `Select` is populated with active accounts
- To-account `Select` excludes the currently selected from-account
- ASSET → ASSET transfer: from delta = −amount, to delta = +amount
- ASSET → LIABILITY transfer: from delta = −amount, to delta = −amount
- Selecting the same account for from and to: error shown, submit disabled or rejected
- Valid transfer: both balances updated atomically in one `UoW` context
- Missing balance for an account/month: a new `Balance` record is inserted with the delta amount
- Cancelling leaves balances unchanged
- After successful transfer, `BalanceUpdateScreen` refreshes table and net worth

**`BalanceUpdateScreen` bindings**
- `r` binding pushes `RollForwardScreen`
- `t` binding pushes `TransferScreen`
- Existing `escape` and `m` bindings continue to work

---

## Manual Validation Steps

### Roll balances forward

1. Navigate Home → Balances; note the current month in the header
2. Press `r` — `RollForwardScreen` opens showing source and computed target month
3. Press Escape → returns to balance update screen, no data written
4. Press `r` again → confirm → success notification; balance update screen now shows the target month with copied balances
5. Run `nwtrack balances update` CLI and verify the same target month appears

### Transfer between accounts

1. Navigate Home → Balances
2. Press `t` — `TransferScreen` opens with current month pre-populated
3. Select a from-account and the same account as to-account → error shown
4. Select different accounts; enter amount → preview shows correct deltas
5. Press Escape → returns to balance update screen, no data written
6. Open transfer again; fill in valid inputs → Ctrl+S → confirm → balances updated; table refreshes

### Navigation

1. `r`, `t` on empty balance table (no months) → handled gracefully (no crash)
2. Escape from any operation screen → returns to balance update screen
3. Escape from `RollForwardScreen` mid-way → no balances written
4. Escape from `TransferScreen` → no balances written

---

## Error and Edge Cases

| Scenario | Expected behaviour |
|---|---|
| Roll-forward when target month already has balances | Error notification; operation blocked |
| Roll-forward with no existing balance data | Notification: no source month available |
| Transfer: from and to accounts are the same | Error label shown; submit blocked |
| Transfer: amount is zero or negative | Error label shown; submit blocked |
| Transfer: account has no balance for the month | Missing balance treated as 0; new record inserted |
| Transfer: `uow` raises exception | Error notification shown; no partial writes |

---

## Definition of Done

- [x] `just check` passes (ruff, mypy, pytest) — 330 tests pass
- [x] All feature-specific test assertions above pass
- [ ] Manual walkthrough completed for roll-forward and transfer
- [x] `BalanceUpdateScreen` shows `r`, `t` in the footer
- [x] Roll-forward: target month guard (existing balances) works correctly
- [x] Transfer delta semantics verified for all four side combinations
- [x] Spec files committed alongside implementation
