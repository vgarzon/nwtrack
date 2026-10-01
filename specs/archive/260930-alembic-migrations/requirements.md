# Alembic Migrations — Requirements

## Problem

`SchemaManager.ensure_current_schema()` applies compatibility upgrades imperatively
(`Base.metadata.create_all()` plus a single hand-rolled `_ensure_sqlite_legacy_columns()` check
for the `accounts.institution_id` column). This has no concept of migration versions, ordering,
or rollback. As the schema keeps growing, ad-hoc upgrade code becomes increasingly fragile and
every new additive change requires another bespoke inspector-based check hard-coded into
`schema.py`.

## Tool selection (researched during spec interview)

Alembic was confirmed as the migration tool, over two alternatives considered:

- **yoyo-migrations** — lighter, but migrations are raw SQL files, which conflicts with the
  "avoid raw SQL unless justified" standard in `specs/tech-stack.md`.
- **Hand-rolled versioned migrations** (a `schema_version` table + ordered Python functions) —
  zero new dependency, but reinvents rollback/ordering logic that Alembic already provides, and
  is essentially a generalized version of the very shim this feature exists to retire.

**Alembic** is SQLAlchemy-native, supports autogenerate from the existing `Base.metadata`, and —
critically for this project — has built-in **batch mode** for SQLite, which works around
SQLite's lack of native `ALTER TABLE ... DROP/ALTER COLUMN` support by transparently doing a
copy-new-table-and-swap. It is one new dependency but is small, mature, and is the tool this
stack is expected to use.

## Scope

In scope:

- Add `alembic` as a project dependency.
- A migrations environment packaged inside `src/nwtrack/infra/persistence/migrations/` (ships
  with the installed tool via `uv tool install`, not a separate top-level `migrations/`
  directory that would be excluded from the built wheel).
- Alembic configured **programmatically** (an `alembic.config.Config` object built in Python),
  not via a filesystem-discovered `alembic.ini` — the app's `db_file_path` is resolved through
  `Settings` at runtime and the script location is resolved relative to the installed package,
  since `nwtrack` may run from any working directory.
- An initial baseline migration capturing the full current schema (all tables as they exist on
  `devel` today, including `accounts.institution_id`).
- `SchemaManager.ensure_current_schema()` delegates schema application to Alembic
  (`command.upgrade(cfg, "head")`) instead of `Base.metadata.create_all()` +
  `_ensure_sqlite_legacy_columns()`.
- `SchemaManager.create_all_tables()` (used by `init_database()`, the destructive
  drop-and-recreate path) still creates the current schema directly, then stamps the resulting
  fresh database at `head` so it is tracked by Alembic from that point on.
- Existing-installation upgrade path (see Decisions below): detect an untracked database on
  first run after this change and adopt it into Alembic version tracking automatically, with no
  user action required and no data loss.
- Retirement of `_ensure_sqlite_legacy_columns()` and the ad-hoc inspector-based column check —
  replaced by a proper versioned migration.
- `nwtrack admin seed-status-history` is unaffected: it remains a data migration distinct from
  Alembic's schema migrations, per the backlog item's stated outcome.

Out of scope:

- Alembic autogenerate is not wired into a CLI command in this feature; migrations are authored
  by hand (the initial baseline plus, going forward, one per schema-changing feature). Wiring
  `alembic revision --autogenerate` into `just`/CLI tooling for developer convenience can be a
  follow-up if it turns out to be useful.
- No change to `nwtrack admin seed-status-history`'s behavior.
- No change to CSV import/export behavior.
- Downgrade/rollback commands are not exposed to end users in this feature (single-user local
  tool; "undo" today means restoring the DB file from a backup or re-importing CSV). The
  `downgrade()` function is still implemented on each migration, since Alembic requires it, but
  no user-facing command invokes it.

## Decisions

- **Migration tool**: Alembic (see Tool selection above).
- **Existing-installation upgrade path**: auto-detect and stamp on startup. Every `nwtrack`
  invocation already calls `ensure_database()` (via `DBAdminService`) before doing anything
  else. When `ensure_current_schema()` runs and finds no `alembic_version` table:
  - If the database has no tables at all (fresh install), run `upgrade head` normally — Alembic
    creates the full schema from the migration chain.
  - If the database has tables but is missing `accounts.institution_id` (a pre-institution_id
    install), stamp it at the baseline revision that predates that column, then run
    `upgrade head` so the institution_id migration (and anything after it) applies for real.
  - If the database already has the full current schema (an up-to-date `devel` checkout that
    predates this feature), stamp it directly at `head` — no schema change, just adopting
    version tracking.
  - This detection lives in `SchemaManager`, is idempotent, and requires no new CLI command or
    user action.
- **Shim retirement**: `_ensure_sqlite_legacy_columns()` is removed in this same feature, not
  kept as a parallel fallback. Its one piece of logic (adding `institution_id`) becomes the
  first real Alembic migration after the baseline.
- **Migrations location**: inside the installed package (`src/nwtrack/infra/persistence/
  migrations/`), not a top-level repo directory, so `uv tool install git+<repo>` ships them.

## Migration safety

These are best-practice gaps identified after the initial draft of this spec and are now
in scope:

- **Backup before migrating**: `ensure_current_schema()` runs on every `nwtrack` invocation, so
  an existing user's file-backed database gets upgraded automatically and silently the first
  time they run any command after updating. Before applying any step that would actually change
  an existing database's schema, take a consistent on-disk snapshot of the database file using
  SQLite's `VACUUM INTO` command issued over a raw connection — this is the one justified
  exception to the "avoid raw SQL" standard, parallel to how `infra/db/sqlite/manager.py`
  already issues raw `PRAGMA` statements, because it is a snapshot/backup mechanism, not
  business-logic querying, and is the only SQLite-correct way to get a consistent copy
  regardless of journal mode. The backup is written next to the live DB file as
  `<db_file_path>.bak-<timestamp>` and is never deleted automatically (the user owns cleanup,
  consistent with "Local Ownership" in `specs/mission.md`). Skipped in three cases, none of
  which puts existing data at risk: a brand-new database with no tables at all (nothing to
  protect — the full schema is simply created from scratch), a database that is already fully
  current and only needs to be stamped with no DDL applied, and `:memory:` databases (tests).
  (This refines the original draft, which proposed also backing up the brand-new-database case;
  implementation showed that produces a pointless backup file on every fresh install with
  nothing in it, so the rule was narrowed to only back up when a real schema change is about to
  touch a database that already has tables.)
- **Failure policy**: if `upgrade head` (or the stamp step) raises, `ensure_current_schema()`
  must not swallow the error or leave the application silently running against a
  partially-migrated database. It propagates the failure with a message that names the backup
  file just taken and instructs the user to restore it if needed, and the calling CLI/TUI
  startup path surfaces that message and exits non-zero rather than continuing.
- **Migration authoring convention** (for future feature specs, documented in `CLAUDE.md` /
  `specs/tech-stack.md`, not enforced in code): every schema-changing feature spec adds exactly
  one new Alembic revision under `versions/`, authored or reviewed by hand even when generated
  via `alembic revision --autogenerate`, and the feature's own `validation.md` must prove the
  migration applies cleanly against a representative pre-migration database shape, in addition
  to the usual `ruff`/`mypy`/`pytest` gates.

## Context

- Per `specs/tech-stack.md`: "Avoid raw SQL unless there is a justified performance or
  expressiveness need." Alembic migrations should use `op.*` operations (`op.add_column`,
  `op.create_table`, etc.) and SQLAlchemy Core constructs, not raw SQL strings, mirroring how
  the rest of the codebase avoids raw SQL.
- Per `specs/tech-stack.md`: quality gates are `ruff`, `mypy`, `pytest` — all must pass.
- The existing `SchemaManager` protocol (`application/ports/schema.py`) and its SQLAlchemy
  implementation (`infra/persistence/schema.py`) stay in place as the port/adapter boundary;
  Alembic is an implementation detail behind `SchemaManager`, not something use cases or the CLI
  import directly.
- `ensure_database()` is called on every CLI invocation (`entrypoints/cli/app.py`) and from
  `init_db_csv` / `import_tables_csv` use cases — the auto-stamp detection above must be cheap
  enough to run unconditionally on every startup (a couple of `inspect()` calls, not a full
  table scan).
- Test fixtures (`tests/conftest.py`) build schemas via `Base.metadata.create_all()` directly
  against `:memory:` SQLite for speed/isolation — this is explicitly preserved per the backlog
  item's stated outcome and must not be routed through Alembic.
