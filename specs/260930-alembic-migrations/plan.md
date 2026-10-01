# Alembic Migrations — Plan

## 1. Dependency and package layout

1.1. Add `alembic` to `[project.dependencies]` in `pyproject.toml`; run `uv sync`.

1.2. Create `src/nwtrack/infra/persistence/migrations/` containing:
   - `env.py` — builds the target `MetaData` from `nwtrack.infra.persistence.orm.base.Base`,
     reads the DB URL from the `Config` object passed in at runtime (not from an ini file or
     env var), and enables `render_as_batch=True` unconditionally (SQLite is the only supported
     dialect today, per `specs/tech-stack.md`).
   - `script.py.mako` — the standard Alembic revision template.
   - `versions/` — migration scripts, starting with the baseline (task 2).

1.3. Confirm (via `uv build` or `just tool-install`) that these non-`.py` files
   (`script.py.mako`) and the `versions/` package are included in the built wheel under the
   `uv_build` backend — add explicit package-data config only if they're excluded by default.

## 2. Baseline and first real migration

2.1. Write `versions/0001_baseline.py`: creates every table exactly as `Base.metadata` defines
   it today (all of `currencies`, `categories`, `institutions`, `tags`, `accounts` — including
   `institution_id` — `account_status_history`, `balances`, `account_tags`,
   `exchange_rates`). Author via explicit `op.create_table(...)` calls (or
   `op.create_table` generated once via autogenerate against an empty DB and hand-checked),
   not raw SQL. `down_revision = None`.

2.2. Write `versions/0002_pre_institution_id_baseline.py` as a second **base-adjacent**
   revision only if needed to model the pre-institution_id historical shape for stamping old
   databases — see task 4. (Decide during implementation whether this is better modeled as a
   distinct earlier revision in the same chain, e.g. `0001` = pre-institution_id shape,
   `0002` = adds `institution_id` via `op.add_column` in batch mode, so real upgrade path and
   stamp-detection share one linear history instead of a synthetic baseline. Prefer this
   simpler linear-chain shape over a branching one.)

2.3. Confirm `alembic upgrade head` against a fresh in-memory/temp SQLite file produces a
   schema identical (same tables/columns/constraints) to today's `Base.metadata.create_all()`
   output — write a test asserting this (see Validation plan).

## 3. `SchemaManager` integration

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

## 4. Existing-installation upgrade detection

4.1. Implement the three-way detection described in requirements.md as a small pure function
   (e.g. `_detect_stamp_revision(inspector) -> str | None`) that is unit-testable without a
   real Alembic run: returns `None` (no stamp needed, just upgrade), the pre-institution_id
   revision id, or `"head"`.

4.2. Wire it into `ensure_current_schema()` ahead of the `upgrade head` call.

## 5. Backup and failure handling

5.1. Add a small helper (e.g. `infra/persistence/backup.py`) with a `backup_before_migration(
   engine) -> Path | None` function: no-ops for `:memory:` / non-file SQLite URLs; otherwise
   issues `VACUUM INTO '<db_file_path>.bak-<timestamp>'` over a raw DBAPI connection and returns
   the backup path.

5.2. Call it from `ensure_current_schema()` immediately before any step that would actually
   change schema (the no-tables-yet `upgrade head` case and the pre-institution_id stamp+upgrade
   case) — not before a no-op "already current, just stamp head" case.

5.3. Wrap the stamp/upgrade calls so that on exception, the error message includes the backup
   path (when one was taken) and re-raises; do not catch-and-continue. Confirm the CLI's startup
   path (`entrypoints/cli/app.py`) lets this propagate as a clear fatal error rather than a
   traceback with no guidance.

## 6. Tests

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

6.2. Update `tests/services/test_db_admin_service.py`: the two existing tests
   (`test_ensure_database_upgrades_legacy_sqlite_schema`,
   `test_ensure_database_creates_tag_tables_for_legacy_sqlite_schema`) must keep passing against
   the new Alembic-backed implementation — adjust setup/assertions only as needed to match the
   new code path, not the behavior being tested.

6.3. `tests/conftest.py` fixtures are unchanged (still `Base.metadata.create_all()` against
   `:memory:`) — add a regression assertion/comment only if useful; no functional change
   expected.

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
