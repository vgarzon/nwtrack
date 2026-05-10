# Phase 21 Plan: CSV Export Coverage For Institutions And Tags

## 1. Export Contract And Table Coverage

1. Extend the default export table set to include `institutions`, `tags`, and `account_tags`.
2. Remove the current export exclusion that omits `accounts.institution_id`.
3. Define deterministic CSV field order for the newly expanded export contract.

## 2. Export Service Support

1. Update the export service so first-class entity tables export through the existing repository-driven path.
2. Add explicit export handling for `account_tags` because it is an association table rather than a current UnitOfWork repository surface.
3. Keep the exported relationship data normalized and ID-based.

## 3. Command And Workflow Preservation

1. Keep the existing `export tables-csv` CLI command path unchanged.
2. Preserve both interactive and non-interactive export flows.
3. Update user-facing command success output as needed so the richer exported table set is visible.

## 4. Compatibility And Regression Tests

1. Replace older compatibility expectations that asserted institutions, tags, and account-tag files were absent.
2. Add tests proving `accounts.csv` now includes `institution_id`.
3. Add tests proving institution, tag, and account-tag relationship data export correctly and deterministically.

## 5. Validation And Documentation

1. Run the required automated quality gates and export-focused tests.
2. Confirm manual export output matches the documented CSV contract.
3. Document the default export contract change clearly enough that Phase 22 can depend on it without redefining Phase 21 behavior.
