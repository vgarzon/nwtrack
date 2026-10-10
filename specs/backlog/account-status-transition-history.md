---
name: account-status-transition-history
status: idea
---

## Problem

When an account is switched to inactive, only the new status is recorded in
`account_status_history`. If the account has no earlier history row, the HISTORICAL status scope
falls back to `Account.status` for all earlier months, so reports treat the account as inactive
for its whole life (active and historical then look identical).

## Notes

- On a status transition, if the account has no history rows, first insert an `ACTIVE` row at its
  earliest balance month (or its creation month if it has no balances), then the new status row.
- The transition logic is duplicated in `update_account_info.py` and the TUI accounts screen;
  the screen should call the use case so there is a single path.
- Out of scope for now: changing the `_apply_status_scope` fallback for months before an
  account's first history row (a possible later design decision).
- Not yet checked: whether toggling status twice in the same month conflicts with a unique
  constraint on `account_status_history`.
