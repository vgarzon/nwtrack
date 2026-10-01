# Alembic Migrations — Validation

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
     stamp (already-current DB) produces no backup file; a `:memory:` DB never produces one.
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

- From a clean checkout on this branch: `rm -f <db_file_path>` (or point `NWTRACK_DATABASE__DB_FILE_PATH`
  at a scratch file), run `nwtrack accounts list` (or any command) — confirm the DB is created
  fresh, fully functional, with no errors, and `sqlite3 <db> "select * from alembic_version"`
  shows a single row at the head revision.
- Simulate an existing pre-feature installation: check out `devel` (pre-this-branch), run
  `nwtrack accounts create` a couple of times to populate a real file-backed DB, note the data.
  Switch to this branch, run any `nwtrack` command against that same DB file, and confirm:
  - No error or prompt.
  - Existing accounts/balances are all still present and correct.
  - `alembic_version` now exists and is at `head`.
- Simulate an up-to-date-but-untracked installation: on `devel` pre-this-branch, run enough
  commands to exercise the `institution_id` column (e.g. create an account with an institution)
  so the DB already has the full current schema. Switch to this branch, run a command, and
  confirm it stamps straight to `head` with zero structural changes (spot-check via
  `sqlite3 <db> ".schema accounts"` before/after).
- `just tool-install` the branch locally and run a command against a real installed-tool DB to
  confirm the packaged migrations are found at runtime (not just when running from the source
  tree via `uv run`).
- Confirm `nwtrack admin seed-status-history` still works unchanged after the schema-management
  rewrite (it's a data migration, untouched by this feature).
- During the pre-feature-installation simulation above, confirm a `.bak-<timestamp>` file
  appears next to the real DB file before the schema change lands, and that it contains the
  pre-migration data (open it directly with `sqlite3`).
- Confirm the already-current-but-untracked simulation does **not** produce a backup file (no
  actual schema change occurred, only a stamp).

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
