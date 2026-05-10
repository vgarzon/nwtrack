# Phase 22 Validation: CSV Import Command And Round-Trip Foundation

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Import CLI And Workflow Foundation
- [X] Source Bundle Validation
- [X] Database Bootstrap And Import Service Refactor
- [X] Idempotent Persistence Behavior
- [X] Round-Trip And Regression Coverage
- [X] Validation And Documentation

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260510-phase-22-csv-import-command-and-round-trip-foundation/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document defines `import tables-csv` as the Phase 22 CLI surface.
- The requirements document defines the supported source as one directory containing the full standard CSV bundle.
- The requirements document states that the full supported file set is required for this phase.
- The requirements document states that import bootstraps a missing or empty database.
- The requirements document states that import behavior is merge-oriented and idempotent.
- The requirements document defines canonical match keys for each supported table.
- The requirements document states that round-trip consistency depends on the Phase 21 export contract.
- The requirements document states that rows absent from the CSV bundle are not deleted in this phase.

Feature-specific implementation tests required by this phase:

- A CLI smoke test proves `import tables-csv` is registered under the main CLI.
- A workflow test proves non-interactive import succeeds from a valid source directory bundle.
- A workflow test proves interactive import succeeds from the same source directory bundle shape.
- A test proves import creates the database/schema when the target database file is missing.
- A test proves import loads `institutions`, `tags`, and `account_tags` in addition to the legacy tables.
- A test proves imported accounts preserve nullable and populated `institution_id` values.
- A test proves imported account-tag relationships match the CSV bundle exactly.
- A test proves re-importing the same bundle does not create duplicate rows or duplicate account-tag associations.
- A round-trip test proves `export tables-csv` followed by `import tables-csv` into a fresh database reproduces equivalent supported data.
- A regression test proves import no longer depends on dropping and recreating all tables for the supported command path.
- A failure test proves a missing required CSV file aborts before partial mutation.
- A failure test proves an invalid source directory fails clearly.
- A failure test proves malformed CSV headers fail clearly.
- A failure test proves invalid relationship references fail clearly.

## Manual

1. Populate a local database with institutions, tags, linked accounts, balances, exchange rates, and account-tag associations.
2. Run `nwtrack export tables-csv` to create a complete Phase 21 CSV bundle.
3. Point `NWTRACK_DB_FILE_PATH` at a fresh database path and run `nwtrack import tables-csv` in CLI mode against that bundle.
4. Confirm the fresh database is created automatically and the imported data is visible through the existing CLI list and report surfaces.
5. Re-run the same import against the same database and confirm there is no visible duplication.
6. Run `nwtrack import tables-csv --interactive` and confirm the interactive path accepts the same source directory shape.
7. Remove one required CSV file from a copy of the bundle and confirm import fails before changing database data.
8. Corrupt one required CSV header in a copy of the bundle and confirm import fails clearly.
9. Confirm `accounts` still reference the expected institutions and `account_tags` still reference the expected tags after import.

## Tone Check

- The spec uses precise CLI-first language rather than abstract ETL terminology.
- The import contract is described concretely enough that implementation and tests can share the same expectations.
- Idempotent merge behavior is explicit rather than implied.
- The round-trip goal is stated as a supported product behavior, not just a testing convenience.

## Definition Of Done

- The Phase 22 spec directory exists with the three required documents.
- The spec clearly defines the `import tables-csv` CLI surface and its directory-bundle input contract.
- The spec clearly defines idempotent merge behavior, database bootstrap behavior, and round-trip expectations.
- The spec locks canonical match keys for supported tables so implementation does not need to invent identity rules.
- The spec names the automated tests, manual checks, and quality gates needed to validate the feature.
