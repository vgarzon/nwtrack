# Phase 32 Plan: Account Status History

## Task Groups

### 1. ORM model + schema migration ✓

1.1 Add `AccountStatusHistory(MappedAsDataclass, Base)` to `orm/models.py`  
  - Fields: `id` (PK, init=False), `account_id` (FK→accounts.id), `status` (Status enum),
    `effective_month` (MonthType)  
  - `__table_args__`: UniqueConstraint(`account_id`, `effective_month`)  
1.2 Re-export `AccountStatusHistory` from `domain/models.py`  
1.3 Update `SchemaManager.ensure_current_schema()` to call `_seed_account_status_history()`
    after `create_all`  
1.4 Implement `_seed_account_status_history()`:
  - Skips if `account_status_history` table does not exist (defensive)  
  - Uses raw SQL `INSERT OR IGNORE INTO account_status_history (account_id, status, effective_month)
    SELECT a.id, a.status, COALESCE(MIN(b.month), '1900-01')
    FROM accounts a LEFT JOIN balances b ON b.account_id = a.id
    WHERE a.id NOT IN (SELECT DISTINCT account_id FROM account_status_history)
    GROUP BY a.id, a.status`  
  - Idempotent: safe to call repeatedly

---

### 2. Repository + UoW wiring ✓

2.1 Create `AccountStatusHistoryRepository` in
    `infra/persistence/repositories/account_status_history.py`  
  - `insert(entry: AccountStatusHistory) -> int`  
  - `get_all() -> list[AccountStatusHistory]`  
  - `get_effective_status(account_id: int, month: Month) -> Status | None`  
  - `hydrate(record: dict) -> AccountStatusHistory`  
  - `hydrate_many(records: list[dict]) -> list[AccountStatusHistory]`  
  - `insert_many(entries: list[AccountStatusHistory]) -> None`  
2.2 Add `AccountStatusHistoryRepository` protocol to `application/ports/repos.py`  
2.3 Add `account_status_history: AccountStatusHistoryRepository` to `UnitOfWork` protocol  
2.4 Update `SQLAlchemyUnitOfWork.__enter__` to instantiate `AccountStatusHistoryRepository`

---

### 3. HISTORICAL scope + reporting queries

3.1 Add `AccountStatusScope.HISTORICAL = "historical"` to `application/dto.py`  
3.2 Update `ReportingQueries._apply_status_scope` to handle `HISTORICAL`:
  - Build correlated scalar subquery: select `AccountStatusHistory.status` where
    `account_id == Account.id` and `effective_month <= Balance.month`, order by
    `effective_month DESC`, limit 1  
  - Apply: `WHERE COALESCE(subquery, Account.status) == Status.ACTIVE`  
  - No signature change needed — using `Balance.month` (ORM column) as the
    correlation variable works for both single-month and history queries  
3.3 Update CLI `--status-scope` options in `entrypoints/cli/commands/reports.py`
    to accept `historical` as a valid choice alongside `active` and `all`

---

### 4. CSV export + import

4.1 Add `"account_status_history"` to `ExportCSV._table_names` and
    `_field_orders` (fields: `id`, `account_id`, `status`, `effective_month`)  
4.2 Add `"account_status_history"` to `InitDataService.IMPORT_TABLE_NAMES`,
    `IMPORT_HEADERS` (header: `id`, `account_id`, `status`, `effective_month`),
    and `IMPORT_ENTITY_TABLE_NAMES`

---

### 5. Tests

5.1 `tests/sqlite/test_account_status_history_repo.py`  
  - `insert` + `get_all` round-trip  
  - `get_effective_status`: returns correct status for exact month match  
  - `get_effective_status`: returns most recent prior row when no exact match  
  - `get_effective_status`: returns None when no row exists at or before the month  
  - `hydrate` / `hydrate_many` round-trip  

5.2 `tests/sqlite/test_schema_migration.py` (or additions to existing)  
  - Seeding creates one row per account with correct status and earliest month  
  - Seeding is idempotent (second call does not duplicate rows)  
  - Seeding with accounts with no balances uses `'1900-01'` sentinel  

5.3 `tests/sqlite/test_reporting_queries.py` additions  
  - `HISTORICAL` scope on single-month aggregation: includes account active in that
    month, excludes account inactive in that month  
  - `HISTORICAL` scope on history aggregation: per-month filtering — account included
    in months where it was active, excluded in months where inactive  
  - COALESCE fallback: account with no history row still filtered by `Account.status`  

5.4 `tests/use_cases/test_export_tables_csv.py` / `test_import_tables_csv.py` additions  
  - Export includes `account_status_history.csv`  
  - Import round-trip preserves rows  

---

## Recommended Implementation Order

Groups 1 → 2 → 3 → 4 → 5.  
Groups 3 and 4 are independent once Group 2 is done.
