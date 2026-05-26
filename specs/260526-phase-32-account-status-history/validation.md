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

**Schema seeding**
- After `ensure_current_schema()` on a database with accounts and balances:
  each account has exactly one seeded row with `status == account.status` and
  `effective_month == earliest balance month for that account`
- After `ensure_current_schema()` on an account with no balances:
  seeded row has `effective_month == '1900-01'`
- Second call to `ensure_current_schema()` does not create duplicate history rows
  (idempotency)

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

1. Run `nwtrack` against an existing database
2. Open SQLite: `SELECT * FROM account_status_history LIMIT 10;`
3. Verify one row per account exists with correct status and an `effective_month`
   matching the account's earliest balance record

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
| Account with no balances | Seeded row has `effective_month = '1900-01'` |
| HISTORICAL scope, no history rows for account | COALESCE falls back to `Account.status` |
| HISTORICAL used with ALL other report types | Correlated subquery filters correctly |
| Duplicate seed call | `INSERT OR IGNORE` prevents duplicates; no error |
| Import with existing rows | `session.merge` is idempotent |

---

## Definition of Done

- [x] `just check` passes (ruff, mypy, pytest) — 323 tests pass
- [x] All feature-specific test assertions above pass
- [ ] Manual seeding check completed
- [x] `nwtrack reports` commands accept `--status-scope historical` (StrEnum-based)
- [x] CSV export includes `account_status_history.csv`
- [x] Spec files committed alongside implementation
