# Phase 32 Requirements: Account Status History

## Problem

Phase 20 improved historical accuracy by including all accounts unconditionally
(`AccountStatusScope.ALL`), which works as long as inactive accounts carry zero
balances. The root cause was never addressed: the data model has no record of
*when* an account's status changed. Without that record, there is no way to
include accounts that were active in a given historical month while excluding
accounts that were already inactive.

## Scope

### What this phase covers

- A new `account_status_history` table records the status that became effective
  for each account starting from a given `YYYY-MM` month
- A migration seeds one initial row per existing account from the current status
  and earliest balance month
- A new `AccountStatusScope.HISTORICAL` filter applies per-month effective status
  to all aggregation queries via a correlated subquery with fallback to `Account.status`
- All CLI `--status-scope` flags accept the new `historical` value
- `account_status_history` is included in CSV export and import

### What this phase does NOT cover

- Automatic history row creation when `Account.status` changes via TUI/CLI update
  workflows (TUI and CLI account update do not insert history rows in this phase;
  this is a follow-on gap documented in decisions)
- Changing the default scope of any existing report command (HISTORICAL is opt-in
  via `--status-scope historical`)

---

## Data Model

### `account_status_history` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | auto-increment |
| `account_id` | INTEGER FK → accounts.id | required |
| `status` | ENUM('active','inactive') | required |
| `effective_month` | TEXT 'YYYY-MM' | required |

Unique constraint: `(account_id, effective_month)`.

One row per account per status-change event. The effective status for account A
at month M is the `status` from the row with the greatest `effective_month ≤ M`.

---

## Decisions

### D1 — Correlated subquery with COALESCE fallback

`HISTORICAL` scope uses a correlated scalar subquery against
`account_status_history` joined on `account_id` and `effective_month ≤ Balance.month`,
ordered descending by `effective_month`, limited to 1 row.

`COALESCE(subquery, Account.status)` falls back to `Account.status` when no
history row exists for an account. This makes the migration and the new scope
safe to use immediately, before any status-change history accumulates beyond
the seeded rows.

Using `Balance.month` (the ORM column) as the correlation variable means the
same `_apply_status_scope` code path works for both single-month and history
queries without a signature change.

### D2 — Seeding: current status + earliest balance month

The migration seeds one row per account:
- `status` = `Account.status` at migration time
- `effective_month` = the earliest month from `balances` for that account, or
  `'1900-01'` as a sentinel when the account has no balance records

Seeding is idempotent: accounts that already have a row in `account_status_history`
are skipped. The seeding runs inside `SchemaManager.ensure_current_schema()` so it
fires automatically on startup.

### D3 — HISTORICAL does not replace default scopes

Existing defaults (`ALL` for networth-history, `ACTIVE` for single-month
aggregation) are unchanged. `HISTORICAL` is a new opt-in scope value.

### D4 — Status-change tracking gap is deferred

When a user updates an account's status (via CLI or TUI), no new
`account_status_history` row is inserted in this phase. This means the seeded
row remains the only history entry. The result is still more accurate than
`ACTIVE` (which uses current status for all history) because the seeded row
captures the status at the earliest known point. Full status-change tracking
(inserting a row every time status changes) is deferred to a follow-on phase.

### D5 — CSV export/import

`account_status_history` is added to the export table list (field order:
`id`, `account_id`, `status`, `effective_month`) and to the import bundle
(header: same four fields). It follows the existing entity-table pattern:
`hydrate_many` + `session.merge` for idempotent import.

---

## Context

### Existing patterns to follow

- ORM models use `MappedAsDataclass`, `MonthType` for YYYY-MM columns, `id: Mapped[int] = mapped_column(init=False)`
- Repositories follow `get_all()`, `insert()`, `hydrate()`, `hydrate_many()` conventions
- `SchemaManager.ensure_current_schema()` uses raw `ALTER TABLE` / `INSERT OR IGNORE` for compatibility migrations
- `AccountStatusScope` is defined in `application/dto.py` as a `StrEnum`
- `_apply_status_scope` is a private helper on `ReportingQueries`; all query methods route through it
