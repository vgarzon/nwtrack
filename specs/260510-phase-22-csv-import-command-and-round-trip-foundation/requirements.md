# Phase 22 Requirements: CSV Import Command And Round-Trip Foundation

## Scope

This phase adds a first-class CSV import workflow to the main CLI and defines the supported round-trip contract for the current normalized table export format.

Included in this phase:

- Add a new `import tables-csv` CLI command under a new top-level `import` command group
- Support both non-interactive CLI import and interactive prompt-driven import
- Import from one source directory containing the standard exported CSV bundle
- Create the database file and current schema when starting from a missing or empty database
- Extend the current CSV initialization/import path to support `institutions`, `tags`, and `account_tags`
- Define idempotent import behavior for the supported CSV bundle
- Define export/import round-trip consistency for the supported tables
- Replace the current destructive reset-oriented CSV initialization behavior with a merge-oriented import workflow for the supported command path

Not included in this phase:

- Selective import of only some supported tables
- Delete-or-sync behavior for rows missing from the CSV bundle
- Support for legacy wide CSV layouts or older ad hoc import file shapes
- Alternate backup formats such as SQL dumps, archives, or JSON
- Bulk transformation or migration of arbitrary third-party CSV formats
- New reporting behavior

### Import CLI Surface

This phase introduces a first-class CLI entrypoint instead of keeping CSV import as an internal module-only initializer.

Required command:

- `import tables-csv`

CLI expectations for this phase:

- A new top-level `import` Typer command group exists in the main `nwtrack` CLI.
- `import tables-csv` supports non-interactive CLI usage with a source directory argument.
- `import tables-csv` also supports an interactive mode that prompts for the source directory, following the existing export interaction pattern.
- The public import contract is a directory bundle, not one CLI argument per file.
- The command should validate the source directory and required files before mutating database data.

### Supported CSV Bundle

The supported import bundle for this phase is one directory containing all of the following files:

- `currencies.csv`
- `categories.csv`
- `institutions.csv`
- `tags.csv`
- `accounts.csv`
- `account_tags.csv`
- `balances.csv`
- `exchange_rates.csv`

The import workflow should treat this directory as one coherent portability bundle.

### Required File Set

Phase 22 requires the full supported bundle.

- Missing any supported CSV file is a validation error.
- Import should fail clearly before partial mutation if the bundle is incomplete.
- This phase does not define optional or best-effort imports for omitted tables.

### CSV Shapes In Scope

This phase imports the Phase 21 export contract as-is.

| File | Fields | Notes |
|------|--------|-------|
| `currencies.csv` | `code,description` | Natural-keyed by `code` |
| `categories.csv` | `name,side` | Natural-keyed by `name` |
| `institutions.csv` | `id,name,description` | ID-keyed |
| `tags.csv` | `id,name,description` | ID-keyed |
| `accounts.csv` | `id,name,description,category,institution_id,currency,status` | ID-keyed, nullable `institution_id` |
| `account_tags.csv` | `account_id,tag_id` | Composite relationship key |
| `balances.csv` | `id,account_id,month,amount` | ID-keyed |
| `exchange_rates.csv` | `id,currency,month,rate` | ID-keyed |

### Identity And Matching Rules

This phase locks the canonical matching rules for idempotent import.

| Table | Canonical match key |
|-------|---------------------|
| `currencies` | `code` |
| `categories` | `name` |
| `institutions` | `id` |
| `tags` | `id` |
| `accounts` | `id` |
| `balances` | `id` |
| `exchange_rates` | `id` |
| `account_tags` | `(account_id, tag_id)` |

Additional rules:

- Relationship references stay ID-based.
- This phase does not remap institutions, tags, accounts, balances, or exchange rates by names when exported IDs are present.
- Natural keys remain the canonical identity only for tables that already use natural primary keys in the product model.

### Import Semantics

#### Database And Schema Bootstrap

- Import must ensure the database file exists and the current schema is available before loading CSV data.
- Starting from a missing database path must be supported.
- Starting from an empty database file must be supported.
- This phase should rely on the existing runtime schema management conventions rather than inventing a separate schema versioning path for import.

#### Idempotent Merge Behavior

The supported import behavior for this phase is upsert-style merge, not destructive replacement.

- Rows present in the CSV bundle are inserted when they do not already exist by canonical match key.
- Rows present in both the CSV bundle and the database are updated from the CSV data.
- Re-importing the same bundle should not create duplicates or relationship drift.
- Import should not drop and recreate all tables as part of normal operation.
- Rows already present in the database but absent from the CSV bundle remain unchanged in this phase.

#### Relationship Preservation

- `accounts.csv` must preserve `institution_id` links exactly.
- `account_tags.csv` must preserve account-to-tag associations exactly.
- Balance rows and exchange-rate rows must preserve the exported IDs and referenced foreign keys needed for round-trip consistency.

#### Round-Trip Consistency

The supported round-trip guarantee for this phase is:

1. Export a supported CSV bundle from database A using `export tables-csv`.
2. Import that bundle into an empty or missing database B using `import tables-csv`.
3. Database B contains the same supported table data as database A for the imported tables.
4. Re-importing the same bundle into database B does not change the resulting supported data.

This phase does not define delete semantics for rows in database B that are not represented in the CSV bundle.

### Validation Failures

The import workflow must fail clearly for invalid source input.

Required failure cases:

- Source path does not exist
- Source path is not a directory
- One or more required CSV files are missing
- A required CSV file has malformed headers for the supported bundle contract
- CSV records cannot be hydrated into valid entities
- CSV relationship rows reference missing required parent rows

The spec does not need to lock exact error strings, but failures must be clear enough for CLI troubleshooting and test assertions.

## Decisions

### Decisions Locked In For This Phase

- Phase 22 introduces a new top-level `import` CLI group with `tables-csv`.
- The import workflow supports both CLI and interactive modes.
- The public import input is one source directory containing the standard CSV bundle.
- Phase 22 requires the full supported CSV table set.
- Import behavior is idempotent and merge-oriented rather than destructive reset.
- Import should bootstrap a missing or empty database automatically.
- Exported IDs are the canonical identity for ID-bearing tables.
- Relationship references remain normalized and ID-based.
- `account_tags.csv` is part of the supported round-trip contract.

### Decisions Explicitly Deferred

- Whether a later phase should support partial imports
- Whether a later phase should support delete-or-sync semantics
- Whether the product should support importing older legacy CSV layouts
- Whether the product should support name-based rekeying or reconciliation workflows
- Archive packaging, compression, or alternate portability formats
- Importing arbitrary third-party CSV schemas

## Context

This spec should be interpreted through `specs/mission.md`, `specs/roadmap.md`, and `specs/tech-stack.md`.

Implementation context for this phase:

- The current codebase has a module-level CSV initializer in `init_db_csv.py`, but it is destructive, not wired into the main CLI, and still scoped around the older table set.
- The current export workflow already emits the richer Phase 21 bundle needed for round-trip support.
- The persistence model already contains first-class repositories for currencies, categories, institutions, tags, accounts, balances, and exchange rates, plus a direct SQLAlchemy association table for `account_tags`.
- The product constitution now treats CSV portability as a backup and recovery workflow, so Phase 22 should make import match that direction rather than remain a legacy-only bootstrap tool.

Tone and implementation expectations:

- Use precise CLI-first language.
- Favor direct, validated import behavior over clever inference.
- Keep the workflow aligned with existing export command patterns where practical.
- Treat idempotency and round-trip consistency as first-class product behavior, not implementation details.
