# Startup Balance Check — Plan

## 1. Application logic — DONE

Implemented as `Month.months_through`, `BalancesRepository.copy_active_by_month` (ORM
`insert().from_select()` with `on_conflict_do_nothing`, no raw SQL) and
`use_cases/forward_fill_balances.py` (`ForwardFillBalances`), registered in
`tui_composition.py`. Unit tests for all three were written alongside (covering the
corresponding items of group 3).

1. Add `Month` helpers if missing (e.g. a range/`months_between(start, end)`), with unit tests.
2. Add a repository method on balances to copy source → target restricted to accounts active in
   the target month (ORM/query constructs), insert-if-absent, returning the row count. Extend the
   `BalancesRepository` protocol in `application/ports/`.
3. Add a use case/service (e.g. `ForwardFillBalances`) with:
   - `find_gap(today: Month) -> list[Month]`: `[]` if the database has no balances or the latest
     balance month >= `today`; otherwise `latest+1 .. today`.
   - `run(months: list[Month]) -> OperationResult[int]`: one UoW, fill in order, rollback and
     return failure on any exception or if a month copies zero rows.
4. Resolve it in `bootstrap/tui_composition.py`.

## 2. TUI wiring

1. Inject the service into `NWTrackApp` and call `find_gap` from `on_mount` after pushing
   `HomeScreen`.
2. If the gap is non-empty, push `ConfirmModal` with the months listed and a "Roll forward" /
   "Not now" pair.
3. On approval, run the fill; on success show a notification with the count of months and
   balances created, then push a second `ConfirmModal` offering to open `BalanceUpdateScreen`
   for the current month (reuse the threshold setting).
4. On failure, show an error notification; no data is changed.
5. On decline, do nothing.

## 3. Tests

1. Unit tests for the month range helper and the new repository method (active-only, no
   overwrite, closed account excluded via status history).
2. Use case tests: no balances, current month present, single-month gap, multi-month gap,
   interior closure mid-gap, atomic rollback on failure.
3. TUI tests under `tests/entrypoints/tui/` using the existing patterns: no prompt when up to
   date or empty DB; prompt on gap; decline persists nothing; approve fills and offers the
   update screen.

## 4. Docs and close-out

1. Update `CLAUDE.md` TUI section and `README.md` if user-facing behaviour is described there.
2. Run `just check`.
3. On merge: delete `specs/backlog/startup-balance-check.md`, remove its row from
   `specs/backlog.md`, move this directory to `specs/archive/startup-balance-check/`, and add a
   one-line `CHANGELOG.md` entry.
