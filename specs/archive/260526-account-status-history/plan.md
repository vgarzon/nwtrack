# Phase 32 Plan: Account Status History

## Task Groups

### 1. ORM model + schema migration ✓

1.1 Add `AccountStatusHistory(MappedAsDataclass, Base)` to `orm/models.py`  
  - Fields: `id` (PK, init=False), `account_id` (FK→accounts.id), `status` (Status enum),
    `effective_month` (MonthType)  
  - `__table_args__`: UniqueConstraint(`account_id`, `effective_month`)  
1.2 Re-export `AccountStatusHistory` from `domain/models.py`  
1.3 `SchemaManager.ensure_current_schema()` creates the `account_status_history` table via
    `Base.metadata.create_all()` — **seeding is not called automatically on startup**  
1.4 Implement public `seed_account_status_history() -> SeedStatusHistoryResult`
    (ORM-based Python loop, no raw SQL):
  - Skips if `account_status_history` table does not exist (defensive)
  - For each account, fetches existing history rows and balance months via ORM
  - **Active accounts**: inserts `(active, first_month)` if no rows exist; otherwise skipped
  - **Inactive accounts, no existing rows, distinct first/last**: inserts
    `(active, first_month)` + `(inactive, last_month)`
  - **Inactive accounts, no existing rows, same/no balance**: inserts
    `(inactive, last_or_sentinel_month)`
  - **Migration path**: a single existing `(inactive, *)` row for an account with a
    distinct last balance month is deleted and replaced with the two-row form
  - Accounts with 2+ history rows are left unchanged (skipped)
  - Safe to call repeatedly
  - Returns `SeedStatusHistoryResult(seeded, migrated, skipped)`

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

### 3. HISTORICAL scope + reporting queries ✓

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

### 4. CSV export + import ✓

4.1 Add `"account_status_history"` to `ExportCSV._table_names` and
    `_field_orders` (fields: `id`, `account_id`, `status`, `effective_month`)  
4.2 Add `"account_status_history"` to `InitDataService.IMPORT_TABLE_NAMES`,
    `IMPORT_HEADERS` (header: `id`, `account_id`, `status`, `effective_month`),
    and `IMPORT_ENTITY_TABLE_NAMES`

---

### 5a. Forward transition recording ✓

5a.1 `create_account.py` — in `_create_account_and_balance`, insert
     `(active, data.initial_month)` history row in the same UoW transaction  
5a.2 `update_account_info.py` — pass `old_status` to `_update_account`; if
     `old_status != update_data.status`, insert `(new_status, current_month)`
     history row in the same UoW transaction  
5a.3 `entrypoints/tui/screens/accounts.py` (`AccountsListScreen`):
  - `action_create`: insert `(active, current_month)` after account creation  
  - `on_data_table_row_selected`: capture `old_status` before mutating `acc`;
    if status changed, insert `(new_status, current_month)` in the same UoW
    transaction

---

### 5b. Admin seed-status-history command ✓

5b.1 Add `SeedStatusHistoryResult` dataclass to `application/dto.py`
     (fields: `seeded: int`, `migrated: int`, `skipped: int`)  
5b.2 Add `seed_account_status_history() -> SeedStatusHistoryResult` to
     `application/ports/schema.py` (`SchemaManager` Protocol)  
5b.3 Add `AdminSeedStatusHistoryPresenter` Protocol to
     `application/ports/presentation.py`  
5b.4 Create `src/nwtrack/application/use_cases/admin_seed_status_history.py`
     (`SeedAccountStatusHistory` class with `run()` + `main()`)  
5b.5 Add `RichAdminSeedStatusHistoryPresenter` to
     `entrypoints/cli/adapters/admin_presenters.py`  
5b.6 Register `nwtrack admin seed-status-history` command in
     `entrypoints/cli/commands/admin.py`

---

### 5. Tests ✓

5.1 `tests/sqlite/test_account_status_history_repo.py`  
  - `insert` + `get_all` round-trip  
  - `get_effective_status`: returns correct status for exact month match  
  - `get_effective_status`: returns most recent prior row when no exact match  
  - `get_effective_status`: returns None when no row exists at or before the month  
  - `hydrate` / `hydrate_many` round-trip  

5.2 `tests/sqlite/test_account_status_history_repo.py` (additions)
  - Seeding creates one row per active account with earliest balance month  
  - Seeding is idempotent (second call does not duplicate rows)  
  - Seeding with accounts with no balances uses `'1900-01'` sentinel  
  - Seeding inactive account with distinct first/last balance months → two rows  
  - Seeding migrates old-style single inactive row → two-row form  

5.3 `tests/sqlite/test_reporting_queries.py` additions  
  - `HISTORICAL` scope on single-month aggregation: includes account active in that
    month, excludes account inactive in that month  
  - `HISTORICAL` scope on history aggregation: per-month filtering — account included
    in months where it was active, excluded in months where inactive  
  - COALESCE fallback: account with no history row still filtered by `Account.status`  

5.4 `tests/use_cases/test_export_tables_csv.py` / `test_import_tables_csv.py` additions  
  - Export includes `account_status_history.csv`  
  - Import round-trip preserves rows  

5.5 `tests/use_cases/test_create_account.py` addition  
  - After successful account creation, `account_status_history` contains one row
    for the new account with `status=ACTIVE` and `effective_month=initial_month`  

5.6 `tests/use_cases/test_update_account.py` additions  
  - Status change from active to inactive inserts a new history row at current month  
  - No history row is inserted when status is unchanged  

5.7 `tests/use_cases/test_admin_seed_status_history.py` (new)  
  - `SeedAccountStatusHistory.run()` returns `OperationResult(success=True)` and
    calls presenter hooks  
  - Seeds accounts that have no history rows  
  - Skips already-seeded accounts; migrates old-style single inactive rows

---

## Recommended Implementation Order

Groups 1 → 2 → 3 → 4 → 5a → 5b → 5.  
Groups 3 and 4 are independent once Group 2 is done.
