# Alembic Migrations — Validation

**Status: complete.** All automated and manual validation below has been run against this
branch; results are noted inline.

## Automated

- `just check` (ruff + mypy + pytest) passes.
- New test file `tests/sqlite/test_alembic_migrations.py` covers, at minimum:
  1. Fresh DB (no file / empty file) → `ensure_current_schema()` produces the full current
     table/column set and stamps `alembic_version` at `head`.
  2. Legacy DB missing `accounts.institution_id`, built without going through Alembic (mirrors
     today's `test_ensure_database_upgrades_legacy_sqlite_schema` setup) →
     `ensure_current_schema()` adds the column via the real migration, preserves existing row
     data in `accounts` and every other table, and ends stamped at `head`.
  3. Legacy DB already at the full current schema but with no `alembic_version` table →
     `ensure_current_schema()` stamps at `head` and makes no structural change (assert table
     DDL is byte-identical before/after, e.g. via `sqlite_master.sql`).
  4. Calling `ensure_current_schema()` a second time on an already-migrated DB is a no-op
     (no exception, no schema change, `alembic_version` unchanged).
  5. A real schema-changing migration (the legacy pre-institution_id case) produces a
     `.bak-<timestamp>` backup file next to the DB containing the pre-migration data; a no-op
     stamp (already-current DB) produces no backup file; a brand-new database with no tables at
     all produces no backup file either (nothing to protect); a `:memory:` DB never produces
     one.
  6. A forced migration failure (monkeypatched) leaves the original DB file byte-for-byte
     unmodified and raises an error whose message names the backup file path.
- Existing tests `tests/services/test_db_admin_service.py::test_ensure_database_upgrades_legacy_sqlite_schema`
  and `::test_ensure_database_creates_tag_tables_for_legacy_sqlite_schema` still pass.
- `tests/conftest.py`'s `base_container` fixture still builds schemas via
  `Base.metadata.create_all()` against `:memory:` SQLite — confirm the full suite still passes
  at the current speed (no fixture regressions from routing test setup through Alembic).
- A test (can live in the new file or a packaging-focused test) asserts the migrations package
  is importable and `versions/` is discoverable at runtime the same way it will be from an
  installed wheel — e.g. resolve the script location via the same helper `SchemaManager` uses,
  rather than a relative path assumption that only works from a source checkout.

## Manual

All run against this branch via the real `nwtrack` CLI (not just unit tests):

- **Fresh install**: pointed `NWTRACK_DATABASE__DB_FILE_PATH` at a new scratch file, ran
  `nwtrack accounts list`. ✅ DB created fresh, fully functional, no errors;
  `alembic_version` shows a single row at `0002` (head); no backup file produced.
- **Legacy pre-institution_id install**: hand-built a real file-backed SQLite DB with the exact
  pre-institution_id shape (currencies/categories/accounts only, one seeded account), ran
  `nwtrack accounts list` against it. ✅ No error; the seeded `cash` account is present and
  correct; all current tables exist (`account_status_history`, `account_tags`, `balances`,
  `exchange_rates`, `institutions`, `tags`); `alembic_version` is at `0002`; a
  `legacy.db.bak-<timestamp>` file was created next to it containing the pre-migration data
  (verified via `sqlite3`). Ran the same command a second time: `alembic_version` unchanged, no
  additional backup file created (idempotent).
- **Already-current untracked install**: covered by the automated test
  (`test_already_current_untracked_database_stamps_without_schema_change`) rather than a
  separate manual run — the automated version already asserts the stronger byte-identical
  `sqlite_master` comparison a manual spot-check would only approximate.
- **Packaged install path**: `just tool-install`, then ran the installed `nwtrack` binary
  (not `uv run`) against a fresh scratch DB. ✅ Migrations were found and applied correctly —
  confirms the packaged `migrations/` directory ships inside the real wheel and is resolved
  correctly at runtime, not just from a source checkout. `just tool-uninstall` afterward to
  restore the environment.
- `nwtrack admin seed-status-history` was not separately re-tested manually since it's
  unchanged code on an unchanged code path (data migration, not schema); covered by its
  existing automated tests which still pass.

## Definition of Done

- `alembic` is a declared dependency; migrations live under
  `src/nwtrack/infra/persistence/migrations/` and ship with the installed package.
- `SchemaManager.ensure_current_schema()` delegates to Alembic; `_ensure_sqlite_legacy_columns()`
  no longer exists anywhere in the codebase.
- A brand-new database, a pre-institution_id legacy database, and an already-current
  untracked database all converge correctly to the same `head` schema with no data loss, with
  no manual step required from the user.
- A pre-migration backup is taken automatically whenever an actual schema change is about to be
  applied (never for no-op stamps, never for `:memory:`), and migration failures abort startup
  with an error naming the backup rather than leaving a half-migrated DB in use.
- All automated and manual validation above passes.
- `ruff`, `mypy`, `pytest` (`just check`) pass.
- `CLAUDE.md`, `specs/tech-stack.md`, and `README.md` all reflect the Alembic-backed schema
  management, the migration-authoring convention, and the automatic-backup behavior, per plan
  task group 7.
