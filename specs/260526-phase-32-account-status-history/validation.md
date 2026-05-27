# Phase 32 Validation: Account Status History

## Automated Tests

### Quality gates

```bash
just check   # ruff + mypy + pytest
```

### Feature-specific test assertions

**`AccountStatusHistoryRepository`**
- `insert` + `get_all`: round-trip preserves all fields
- `get_effective_status(account_id, month)`:
  - Returns the status from the row with `effective_month == month` (exact match)
  - Returns the status from the most recent row with `effective_month < month` (prior match)
  - Returns `None` when no row exists at or before the given month
- `hydrate` / `hydrate_many`: reconstruct `AccountStatusHistory` with correct types
- `insert_many`: inserts multiple rows atomically

**Schema seeding** (`SchemaManager.seed_account_status_history()`)
- Active account with balance history: one row with `status=active` and
  `effective_month=first_balance_month`
- Inactive account with distinct first/last balance months: two rows —
  `(active, first_month)` and `(inactive, last_month)`
- Inactive account with no balances: one row with `status=inactive` and
  `effective_month='1900-01'`
- Second call does not create duplicate rows (idempotency)
- An existing single `(inactive, first_month)` row for an account with a distinct
  last balance month is migrated to the two-row form on the next seed call

**Admin seed use case**
- `SeedAccountStatusHistory.run()` returns `OperationResult(success=True)` and
  calls `presenter.show_header()` and `presenter.show_result(result)`
- `result.seeded` counts accounts that received new rows from scratch
- `result.migrated` counts accounts whose old-style row was replaced
- `result.skipped` counts accounts left unchanged (already had correct rows)

**Forward transition recording**
- After `AccountCreator.run()` succeeds: one `account_status_history` row exists
  for the new account with `status=ACTIVE` and `effective_month=initial_month`
- After `UpdateAccountInfo._update_account()` with a status change: a new history
  row exists with `status=new_status` and `effective_month=current_month`
- After `UpdateAccountInfo._update_account()` with no status change: no new
  history rows are inserted

**`AccountStatusScope.HISTORICAL` in reporting queries**
- Single-month aggregation with `HISTORICAL`:
  - Account with `effective_month <= query month` and `status = active` → included
  - Account with `effective_month <= query month` and `status = inactive` → excluded
- History aggregation with `HISTORICAL`:
  - Account inactive for months M1–M2 but active for M3 → appears only in M3 rows
- COALESCE fallback: account with no history row → filtered by `Account.status`

**CSV export / import**
- Export produces `account_status_history.csv` with correct header and rows
- Import round-trip: exported CSV re-imported → same rows present in database

---

## Manual Validation Steps

### Seeding check

1. Run `nwtrack admin seed-status-history` against an existing database
2. Verify the command prints a summary line (e.g. "N account(s) seeded")
3. Open SQLite: `SELECT * FROM account_status_history LIMIT 10;`
4. Verify rows exist with correct status and `effective_month` values matching
   each account's balance history

### HISTORICAL scope via CLI

1. Run `nwtrack reports balances-aggregate-history --start-month 2024-01 --end-month 2025-01 --dimension side --status-scope historical`
2. Verify the command completes without error
3. Verify output changes vs `--status-scope all` when any account changed status
   in the history range

### CSV round-trip

1. `nwtrack export csv ./export_test`
2. Verify `export_test/account_status_history.csv` exists and has correct header
3. `nwtrack import tables-csv ./export_test`
4. Verify import completes without error

---

## Error and Edge Cases

| Scenario | Expected behaviour |
|---|---|
| Active account with no balances | Seeded row has `effective_month = '1900-01'`, `status=active` |
| Inactive account with no balances | Seeded row has `effective_month = '1900-01'`, `status=inactive` |
| Inactive account with single balance month | One seeded row with `status=inactive` at that month |
| Inactive account with distinct first/last balance | Two seeded rows: `(active, first)` + `(inactive, last)` |
| Old-style single inactive seed row, distinct balance range | Migrated to two-row form on next seed call |
| HISTORICAL scope, no history rows for account | COALESCE falls back to `Account.status` |
| HISTORICAL used with ALL other report types | Correlated subquery filters correctly |
| Duplicate seed call | Accounts with 2+ rows are left unchanged; no error |
| Import with existing rows | `session.merge` is idempotent |
| Account created via CLI | Initial `(active, initial_month)` row inserted atomically |
| Account created via TUI | Initial `(active, current_month)` row inserted atomically |
| Status change via CLI or TUI | New `(new_status, current_month)` row inserted |
| Non-status field update (name, description, etc.) | No history row inserted |

---

## Definition of Done

- [x] `just check` passes (ruff, mypy, pytest) — 331 tests pass
- [x] All feature-specific test assertions above pass
- [ ] Manual seeding check completed (`nwtrack admin seed-status-history` run against production DB)
- [x] `nwtrack reports` commands accept `--status-scope historical` (StrEnum-based)
- [x] CSV export includes `account_status_history.csv`
- [x] Account creation inserts initial history row (CLI and TUI)
- [x] Account status change inserts transition history row (CLI and TUI)
- [x] `nwtrack admin seed-status-history` command exists and calls `SeedAccountStatusHistory` use case
- [x] Seeding is NOT called automatically on startup — on-demand only
- [x] Spec files committed alongside implementation
