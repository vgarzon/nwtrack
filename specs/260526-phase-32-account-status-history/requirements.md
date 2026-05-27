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
- A migration seeds initial rows per existing account based on balance history and
  current status (see D2 for the two-row inactive-account approach)
- Account creation inserts an initial `(active, initial_month)` history row in the
  same transaction as the account and balance, via both CLI and TUI paths
- Account status changes insert a new `(new_status, current_month)` history row in
  both the CLI `update_account_info` use case and the TUI `AccountsListScreen`
- A new `AccountStatusScope.HISTORICAL` filter applies per-month effective status
  to all aggregation queries via a correlated subquery with fallback to `Account.status`
- All CLI `--status-scope` flags accept the new `historical` value
- `account_status_history` is included in CSV export and import

### What this phase does NOT cover

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

### D2 — Seeding: inferred history from balance range and current status

The migration seeds rows per account using the following assumptions:
- All accounts were active at the time of their first balance entry.
- No account has transitioned between active and inactive more than once.
- Currently inactive accounts became inactive at their last balance month.

Resulting seed logic:
- **Active accounts**: one row `(active, first_balance_month)`, or `(active, '1900-01')`
  if no balances exist.
- **Inactive accounts with distinct first/last balance months**: two rows —
  `(active, first_balance_month)` and `(inactive, last_balance_month)`.
- **Inactive accounts with a single balance month or no balances**: one row
  `(inactive, that_month_or_'1900-01')`.

The seeding also migrates old-style seeded rows: a single `(inactive, first_month)`
row for an account that has a distinct last balance month is replaced with the
two-row form above.

Seeding is safe to call repeatedly: accounts with more than one history row (i.e.,
rows that were not created by the old single-row seed) are left unchanged. The
seeding runs inside `SchemaManager.ensure_current_schema()` on every startup.

### D3 — HISTORICAL does not replace default scopes

Existing defaults (`ALL` for networth-history, `ACTIVE` for single-month
aggregation) are unchanged. `HISTORICAL` is a new opt-in scope value.

### D4 — Forward transition recording

When a user updates an account's status via `update_account_info` (CLI) or
`AccountsListScreen` (TUI), a new `account_status_history` row is inserted in the
same transaction with `effective_month = current_month`. No row is inserted if the
status did not change.

When a user creates a new account via `create_account` (CLI) or
`AccountsListScreen` (TUI), an initial `(active, initial_month)` history row is
inserted alongside the account and its first balance.

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
- `SchemaManager.ensure_current_schema()` uses ORM-based Python logic for the seeding migration
- `AccountStatusScope` is defined in `application/dto.py` as a `StrEnum`
- `_apply_status_scope` is a private helper on `ReportingQueries`; all query methods route through it
