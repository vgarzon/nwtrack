# Startup Balance Check — Requirements

## Scope

On TUI launch, detect when the database has no balances for the current calendar month and offer
to forward-fill the missing months, with a single user approval.

**Included**

- A startup check that runs once per TUI launch, after `HomeScreen` is mounted.
- Gap detection from the latest month that has balances through the current calendar month
  (`latest+1 .. current`, inclusive).
- A confirmation modal listing the missing months (e.g. `2026-08 → 2026-10, 3 months`).
- On approval, forward-fill each missing month in order: month N is filled from month N-1.
- After a successful fill, offer to open the balance update screen for the current month.
- Declining dismisses the modal; nothing is persisted.

**Not included**

- Gaps in the interior of history (only the trailing gap after the latest balance month).
- A config option to disable the check, or "remember dismissal" state.
- Per-month confirmation.
- Any change to the CLI (`nwtrack balances roll` is unchanged).
- Schema changes — no Alembic migration.

| Input | Source |
|---|---|
| Latest month with balances | `FetchService.get_recent_months(n_months=1)` |
| Current month | system date, as `Month(year, month)` |
| Effective account status per month | `account_status_history` |

## Decisions

1. **Trailing gap only.** Chosen over current-month-only (cannot handle multi-month gaps, the
   user's stated requirement) and full-history gap scan (more scope than the backlog item asks).
2. **Confirm modal, then automatic roll-forward**, reusing `ConfirmModal`. Chosen over opening
   the Roll Forward screen (extra steps, one per month) and per-month prompts.
3. **Skip on an empty database.** With no balances there is no source month to fill from; the
   user is expected to create balances through the normal flow.
4. **Closed accounts are excluded per month.** For each target month, only accounts whose
   effective status (`get_effective_status`) is active in that month are carried forward. This
   differs from `BalancesRepository.copy_by_month`, which copies every row of the source month
   regardless of status, so the fill needs an active-only variant.
5. **Atomic across the whole gap.** All missing months are filled in one unit of work; any
   failure rolls back everything and shows an error. No partially filled gap.
6. **Never overwrite.** Fill uses insert-if-absent semantics (as `copy_by_month` does with
   `INSERT OR IGNORE`).
7. **Runs every launch.** Once the current month has balances the check is a no-op, so no
   persistence of dismissal is needed.
8. **Future current month is not special-cased:** if the latest balance month is >= the current
   month, no prompt is shown.

## Context

- Logic belongs in an application-layer service/use case, not in the screen. The screen only
  calls it and renders modals. Follow the existing patterns: callable `uow` factory,
  `OperationResult[T]`, read-only lookups through `FetchService`.
- Prefer SQLAlchemy ORM/query constructs for the new repository method. `copy_by_month` uses raw
  SQL today; do not extend that precedent without a stated reason.
- Reuse `ConfirmModal` and the shared theme classes in `entrypoints/tui/theme.py`; no new
  structural CSS.
- Wire dependencies through `bootstrap/tui_composition.py`; `NWTrackApp` triggers the check from
  `on_mount` after pushing `HomeScreen`.
- Copy style: short and factual, matching existing modals (e.g. "2026-08 → 2026-10 have no
  balances. Roll forward 3 months from 2026-07?").
- Mission fit: low-friction monthly updates, with accounting correctness preserved by excluding
  closed accounts and by being all-or-nothing.
