# Phase 22 Plan: CSV Import Command And Round-Trip Foundation

## 1. Import CLI And Workflow Foundation

1. Add a new top-level `import` Typer command group.
2. Add an `import tables-csv` command that matches the existing export command style.
3. Support both non-interactive source-directory import and interactive prompt-driven import.

## 2. Source Bundle Validation

1. Define the required standard CSV bundle filenames for Phase 22.
2. Validate the source directory and required files before mutating database data.
3. Validate CSV headers against the supported Phase 21 export contract.

## 3. Database Bootstrap And Import Service Refactor

1. Refactor the current CSV initialization/import path away from destructive reset behavior for the supported CLI workflow.
2. Ensure import creates the database and current schema when starting from a missing or empty database.
3. Extend CSV loading support to include `institutions`, `tags`, and `account_tags`.

## 4. Idempotent Persistence Behavior

1. Implement per-table insert-or-update behavior using the locked canonical match keys from the requirements.
2. Preserve normalized ID-based relationships, including `accounts.institution_id` and `account_tags`.
3. Ensure re-importing the same bundle does not create duplicate rows or duplicate associations.
4. Keep rows absent from the CSV bundle unchanged in this phase.

## 5. Round-Trip And Regression Coverage

1. Add CLI coverage proving `import tables-csv` is registered and callable.
2. Add tests for fresh-database bootstrap, repeat-import idempotency, and invalid bundle failures.
3. Add round-trip tests proving a Phase 21 export bundle imports back into equivalent supported table data.

## 6. Validation And Documentation

1. Run the required automated quality gates and import-focused tests.
2. Confirm the feature spec still matches the implemented workflow and validation cases.
3. Update roadmap/spec status only when implementation of the phase is complete.
