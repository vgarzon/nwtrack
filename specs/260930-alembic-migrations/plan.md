# Alembic Migrations — Plan

## 1. Dependency and package layout — done

1.1. Add `alembic` to `[project.dependencies]` in `pyproject.toml`; run `uv sync`.

1.2. Create `src/nwtrack/infra/persistence/migrations/` containing:
   - `env.py` — builds the target `MetaData` from `nwtrack.infra.persistence.orm.base.Base`,
     reads the DB URL from the `Config` object passed in at runtime (not from an ini file or
     env var), and enables `render_as_batch=True` unconditionally (SQLite is the only supported
     dialect today, per `specs/tech-stack.md`).
   - `script.py.mako` — the standard Alembic revision template.
   - `versions/` — migration scripts, starting with the baseline (task 2).

1.3. Confirmed via `uv build --wheel`: `migrations/` (including `script.py.mako` and
   `versions/`) is included in the built wheel automatically under `uv_build` — no package-data
   config needed. (`env.py` ended up connection-driven only, not URL/ini-driven as 1.2
   originally described — see `alembic_runtime.py` and task 3.1.)

## 2. Baseline and first real migration — done

2.1. Write `versions/0001_baseline.py`: creates every table exactly as `Base.metadata` defines
   it today (all of `currencies`, `categories`, `institutions`, `tags`, `accounts` — including
   `institution_id` — `account_status_history`, `balances`, `account_tags`,
   `exchange_rates`). Author via explicit `op.create_table(...)` calls (or
   `op.create_table` generated once via autogenerate against an empty DB and hand-checked),
   not raw SQL. `down_revision = None`.

2.2. Decided: a single linear chain, not a branching one. `0001_initial_schema` *is* the
   pre-institution_id baseline (matches the legacy fixture in
   `tests/services/test_db_admin_service.py` exactly: currencies, categories, accounts with no
   `institution_id`). `0002_full_current_schema` carries every other delta to the current model:
   creates `institutions`, `tags`, `account_tags`, `balances`, `account_status_history`,
   `exchange_rates`, and adds `accounts.institution_id` via `op.batch_alter_table`. Generated via
   `alembic revision --autogenerate` against a `0001`-stamped temp database, then hand-cleaned
   (missing `MonthType` import; unnamed FK name on `institution_id`). Batch mode's table-args
   must explicitly re-declare `accounts`' existing unnamed `check_account_status` CHECK
   constraint — Alembic's batch reflection silently drops unnamed constraints otherwise, which a
   test against a real legacy fixture caught (`UserWarning: Unnamed CHECK constraint ... is
   being omitted`).

2.3. Confirmed via a scratch comparison script: table and column sets match exactly between
   `upgrade head` and `Base.metadata.create_all()`. Literal `CREATE TABLE` text differs in
   constraint ordering and some `VARCHAR(n)` length annotations (SQLite ignores these — same
   type affinity either way), so the committed regression test
   (`tests/sqlite/test_alembic_migrations.py::test_fresh_database_migrates_to_head_with_full_schema`)
   asserts structural equality (table names, column names/presence) rather than raw DDL text
   equality, which is the correct/standard way to validate this on SQLite.

## 3. `SchemaManager` integration — done

3.1. Add a small internal helper (e.g. `infra/persistence/alembic_runtime.py`) that builds an
   `alembic.config.Config` pointed at the packaged `migrations/` directory (resolved via
   `importlib.resources`/`__file__`, not a relative path assumption) with `sqlalchemy.url` set
   from the engine already held by `SchemaManager`.

3.2. Rewrite `SchemaManager.ensure_current_schema()`:
   - Build the Alembic `Config`.
   - Inspect the current DB for an `alembic_version` table.
   - If absent, run the auto-stamp detection from `requirements.md` (no tables → skip stamping
     and just `upgrade head`; missing `institution_id` → stamp at the pre-institution_id
     revision; else → stamp at `head`).
   - Always finish with `command.upgrade(cfg, "head")`.

3.3. Update `SchemaManager.create_all_tables()` (used by `init_database()`) to, after
   `Base.metadata.create_all()`, stamp the fresh DB at `head` via the same Alembic `Config`
   helper, so a freshly wiped/reinitialized DB is tracked from the start.

3.4. Delete `_ensure_sqlite_legacy_columns()` entirely.

3.5. `application/ports/schema.py` protocol is unchanged (same three methods) — Alembic stays
   an implementation detail of the SQLAlchemy adapter.

## 4. Existing-installation upgrade detection — done

4.1. Implemented `_detect_stamp_revision(inspector) -> str | None` in `schema.py` exactly as
   planned.

4.2. Wired into `ensure_current_schema()` ahead of the head-vs-current comparison.

## 5. Backup and failure handling — done

5.1. Add a small helper (e.g. `infra/persistence/backup.py`) with a `backup_before_migration(
   engine) -> Path | None` function: no-ops for `:memory:` / non-file SQLite URLs; otherwise
   issues `VACUUM INTO '<db_file_path>.bak-<timestamp>'` over a raw DBAPI connection and returns
   the backup path.

5.2. Call it from `ensure_current_schema()` immediately before any step that would actually
   change the schema of a database that already has tables (the pre-institution_id
   stamp+upgrade case, and any future tracked-but-behind-head case). Skip it for a brand-new
   database with no tables at all (nothing to protect) and for the no-op "already current, just
   stamp head" case.

5.3. Done — `ensure_current_schema()` wraps the `upgrade head` call and re-raises as
   `RuntimeError` naming the backup path. `entrypoints/cli/app.py` calls `ensure_database()`
   with no try/except around it, so this propagates as an uncaught fatal error on CLI/TUI
   startup, which is the intended behavior (no silent partial-migration state).

## 6. Tests — done

6.1. `tests/sqlite/test_alembic_migrations.py` (new):
   - Fresh temp-file SQLite DB → `ensure_current_schema()` → assert full expected table/column
     set exists and `alembic_version` is stamped at `head`.
   - Simulated pre-institution_id legacy DB (build schema manually without that column, as the
     existing `test_ensure_database_upgrades_legacy_sqlite_schema` test already does) →
     `ensure_current_schema()` → assert `institution_id` column now exists, data preserved,
     `alembic_version` at `head`.
   - Simulated already-current legacy DB (full schema, no `alembic_version` table) →
     `ensure_current_schema()` → assert it stamps at `head` without altering any table.
   - Idempotency: calling `ensure_current_schema()` twice in a row is a no-op the second time.
   - Backup: migrating a legacy file-backed DB produces a `.bak-<timestamp>` file alongside it
     containing the pre-migration data; migrating an already-current DB (no-op stamp) produces
     no backup file; a `:memory:` DB never produces a backup file.
   - Failure path: force `command.upgrade` to raise (e.g. monkeypatch) and assert the raised
     error message references the backup path, and that the original DB file is unmodified.

6.2. Both existing tests in `tests/services/test_db_admin_service.py` pass unchanged against the
   new Alembic-backed implementation — no edits needed.

6.3. `tests/conftest.py` fixtures unchanged, as planned; full suite (448 tests) passes.

## 7. Documentation

7.1. `CLAUDE.md`:
   - Replace the "Database schema is managed entirely through SQLAlchemy ORM models ... Schema
     creation is handled by `Base.metadata.create_all()`" description (Database Operations
     section) with an Alembic-backed description: migrations live under
     `src/nwtrack/infra/persistence/migrations/`, `ensure_current_schema()` runs them
     automatically on startup, and a pre-migration backup (`<db_file_path>.bak-<timestamp>`) is
     taken automatically whenever an actual schema change is about to be applied.
   - Add a short "Adding a schema migration" note under Code Conventions or Database Operations
     describing the one-migration-per-schema-changing-feature convention from
     `requirements.md`'s Migration safety section, including that `validation.md` for such a
     feature must prove the migration applies against a representative pre-migration DB shape.

7.2. `specs/tech-stack.md`:
   - Record Alembic as a Product Runtime dependency (alongside SQLAlchemy) and note the SQLite
     batch-mode rationale, mirroring how other stack choices are justified in that doc.
   - Add the migration-authoring convention (one revision per schema-changing feature, hand-
     reviewed even when autogenerated) and the automatic-backup-before-migration behavior to
     Engineering Standards or Current Platform Decisions, so future specs inherit the rule
     without re-deriving it.

7.3. `README.md`:
   - Under "Upgrading," add a short note that schema upgrades now happen automatically the next
     time `nwtrack` runs after installing a new version — no manual migration command — and
     that a timestamped backup of the database file is made automatically beforehand (and never
     auto-deleted, so cleanup is the user's own responsibility, consistent with the rest of the
     Configuration section's local-ownership framing).
   - Cross-reference where the backup file appears (same directory as `db_file_path`).
