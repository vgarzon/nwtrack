# Phase 21 Requirements: CSV Export Coverage For Institutions And Tags

## Scope

This phase expands the existing CSV export workflow so the default exported table set reflects the current product data model instead of a legacy-only subset.

Included in this phase:

- Extend the existing `export tables-csv` command and use case to export institution and tag data
- Export account-to-institution linkage by including `institution_id` in `accounts.csv`
- Export account-to-tag linkage through a dedicated `account_tags.csv` file
- Keep the export shape normalized and table-oriented so a later CSV import phase can reconstruct the same relationships
- Define the default CSV export contract for the richer schema needed for portability, backup, and recovery

Not included in this phase:

- A new CSV import CLI command or import workflow
- Idempotent import semantics
- Relationship rekeying by names instead of IDs
- Non-CSV backup formats
- Broader export UX redesign beyond what is needed for the richer output
- Changes to reporting commands or reporting CSV output

### Export CLI Surface

This phase updates the existing export command path rather than adding a new one.

Required command:

- `export tables-csv`

CLI expectations for this phase:

- The default behavior of `export tables-csv` changes to emit the richer table set.
- Interactive and non-interactive command flows remain in place.
- The command still exports one CSV file per supported table into the selected target directory.
- Export output should stay readable as plain normalized table files rather than adding presentation-oriented formatting.

### Exported Table Set

The default exported table set for this phase is:

- `currencies.csv`
- `categories.csv`
- `institutions.csv`
- `tags.csv`
- `accounts.csv`
- `account_tags.csv`
- `balances.csv`
- `exchange_rates.csv`

The export contract should treat this table set as one coherent portability bundle for the supported schema.

### CSV Shapes In Scope

This phase defines the exported CSV shapes needed for full current-state coverage.

| File | Fields | Notes |
|------|--------|-------|
| `currencies.csv` | `code,description` | Unchanged |
| `categories.csv` | `name,side` | Unchanged |
| `institutions.csv` | `id,name,description` | New export file |
| `tags.csv` | `id,name,description` | New export file |
| `accounts.csv` | `id,name,description,category,institution_id,currency,status` | Gains nullable `institution_id` |
| `account_tags.csv` | `account_id,tag_id` | New export file for many-to-many links |
| `balances.csv` | `id,account_id,month,amount` | Unchanged |
| `exchange_rates.csv` | `id,currency,month,rate` | Unchanged |

### Relationship Encoding

This phase uses database IDs as the canonical reference format for exported relationships.

- `accounts.csv` uses nullable `institution_id` to reference `institutions.id`.
- `account_tags.csv` uses `account_id` and `tag_id` to reference existing account and tag rows.
- This phase does not add redundant name columns for relationship convenience.
- The export format should remain aligned with the current normalized repository hydration style rather than inventing a parallel name-keyed contract.

### Workflow Behavior

#### Table Coverage

- The export workflow includes institution, tag, and account-tag data when present.
- The export workflow continues to export the pre-existing tables.
- Empty tables should not cause the command to fail.
- Empty supported tables are reported as skipped and do not produce CSV files.
- Export order should remain deterministic so the resulting directory is stable and easy to inspect.

#### Accounts CSV

- `accounts.csv` now includes `institution_id` in the default header.
- Accounts without an institution export an empty value for `institution_id`.
- Existing account fields remain in the same normalized table export.

#### Account Tags CSV

- `account_tags.csv` contains one row per persisted account-tag association.
- Rows should represent the stored many-to-many association directly rather than a comma-separated list on `accounts.csv`.
- The file should be deterministic and readable enough to support later round-trip validation.

#### Compatibility Posture

- This phase intentionally updates the default export contract instead of preserving the legacy default shape.
- The richer output is the new expected default because local portability now needs to cover institutions and tags.
- Compatibility concerns should be handled through explicit release-note and spec documentation rather than by keeping the legacy export as the default.

## Decisions

### Decisions Locked In For This Phase

- Phase 21 extends the existing `export tables-csv` command instead of adding a separate export path.
- The default CSV export output is allowed to change to the richer schema.
- Institutions and tags are exported as first-class tables.
- Account-to-institution linkage is exported via `accounts.csv`.
- Account-to-tag linkage is exported via `account_tags.csv`.
- Relationship references use database IDs, not names.
- The export contract remains normalized and table-oriented to support a later import phase.
- This phase is the portability foundation for the later CSV import and round-trip work.

### Decisions Explicitly Deferred

- How the later import workflow resolves duplicates or conflicts
- Whether import upserts by ID, natural key, or mixed strategy
- CLI flags for selective table export
- Export compression, archives, or alternate file formats
- Human-friendly denormalized exports that duplicate relationship names
- Any broader migration of historical legacy CSV files into the new format

## Context

This spec should be interpreted through `specs/mission.md`, `specs/roadmap.md`, and `specs/tech-stack.md`.

Implementation context for this phase:

- The current export workflow already exists as `export tables-csv` with interactive and CLI modes.
- The current export service intentionally excludes `accounts.institution_id` and does not emit `institutions.csv`, `tags.csv`, or `account_tags.csv`.
- The current persistence model already has first-class `Institution` and `Tag` entities plus the `account_tags` association table.
- The product now treats CSV portability as a backup and recovery workflow, so the default export contract should reflect the current supported schema rather than a Phase 10 or Phase 13 compatibility subset.

Tone and implementation expectations:

- Use precise CLI-first language.
- Favor a direct normalized export contract over clever convenience formats.
- Treat the richer default export as an intentional product improvement, not an accidental regression.
- Keep the phase independently shippable so Phase 22 can focus on import behavior rather than backfilling missing export coverage.
