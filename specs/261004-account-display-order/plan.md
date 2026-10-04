# Account Display Order — Plan

## 1. Data
1. Add `display_order: Mapped[int]` and `is_hidden: Mapped[bool]` (defaults) to `Account` in
   `orm/models.py`; add unique constraint on `display_order`.
2. Alembic revision `0003`: add both columns (batch mode, explicit `table_args`), backfill
   `display_order` by `id` rank, add unique constraint; author downgrade.
3. `SchemaManager.create_all_tables()` path: confirm fresh DBs get the columns and are stamped
   at head.

## 2. Repository and services
1. `AccountsRepository`: order `get_all`/`get_active` by `display_order`; `insert` assigns
   `max+1`; delete renumbers; add `move(account_id, direction)` and `set_hidden(account_id, bool)`.
2. Balances queries that return per-account rows (`get_month_balances` etc.) join/sort by
   `Account.display_order`.
3. `FetchService`: `get_accounts(..., include_hidden=True)` and `get_month_balances(...,
   include_hidden=True)` parameters; default keeps CLI/report behaviour (nothing hidden).
4. Use case `ReorderAccounts` (move up/down, toggle hidden) returning `OperationResult`.
5. CSV: add the two columns to `accounts` export; import defaults when absent.

## 3. TUI
1. Balance-update table: `include_hidden` toggle key, visible-total line, net-worth label
   unchanged.
2. Accounts list screen and account pickers (transfer, balance create/edit): ordered, hidden
   filtered, toggle where a table is shown.
3. New `account_order.py` admin screen (all accounts, hidden marked, move up/down, toggle
   hidden); wire into `admin_menu.py` and `tui_composition.py`.

## 4. CLI
1. Ensure CLI account/balance listings use the new order (no hiding).

## 5. Tests and docs
1. Repository, migration, service, use case, CSV round-trip and TUI tests (see validation.md).
2. Update `CLAUDE.md` (tables/columns, TUI screens list) and `CHANGELOG.md` at close.
