---
name: alembic-migrations
status: idea
---

## Problem

Replace the current hand-rolled `SchemaManager` with a proper migration tool (Alembic or
equivalent) so that schema evolution is versioned, auditable, and reversible.

The current approach applies compatibility upgrades imperatively in `ensure_current_schema()`.
This works for additive changes (new tables, new nullable columns) but has no concept of
migration versions or rollbacks. As the schema grows and the user base widens, ad-hoc upgrade
code becomes increasingly fragile.

## Expected outcomes

- Alembic integrated as a project dependency with a migration environment under `migrations/`
- An initial migration captures the current full schema as a baseline
- `SchemaManager.ensure_current_schema()` delegates to `alembic upgrade head`
- `nwtrack admin seed-status-history` remains available as a data-migration command distinct
  from schema migrations
- The legacy `_ensure_sqlite_legacy_columns` compatibility shim is retired, replaced by a
  versioned Alembic migration
- `ruff`, `mypy`, and `pytest` pass; existing test fixtures continue to create schemas via
  `Base.metadata.create_all` (test isolation is unchanged)

## Notes

Formerly "Phase 37 (On Hold, Future)" in the old roadmap.
