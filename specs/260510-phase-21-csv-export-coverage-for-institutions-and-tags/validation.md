# Phase 21 Validation: CSV Export Coverage For Institutions And Tags

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Export Contract And Table Coverage
- [X] Export Service Support
- [X] Command And Workflow Preservation
- [ ] Compatibility And Regression Tests
- [ ] Validation And Documentation

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260510-phase-21-csv-export-coverage-for-institutions-and-tags/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document defines `export tables-csv` as the Phase 21 CLI surface.
- The requirements document defines the richer default exported table set, including `institutions.csv`, `tags.csv`, and `account_tags.csv`.
- The requirements document states that `accounts.csv` now includes nullable `institution_id`.
- The requirements document states that relationship references use IDs rather than names.
- The requirements document states that `account_tags.csv` is part of the default export contract.
- The requirements document states that the default export contract is intentionally allowed to change in this phase.

Feature-specific implementation tests required by this phase:

- A CLI smoke test proves `export tables-csv` remains registered.
- A use-case or workflow test proves interactive export writes the richer table set when those tables contain data.
- A use-case or workflow test proves non-interactive export writes the richer table set when those tables contain data.
- A test proves `institutions.csv` is written with `id,name,description`.
- A test proves `tags.csv` is written with `id,name,description`.
- A test proves `accounts.csv` includes `institution_id` in the header and exports empty values for accounts without an institution.
- A test proves `accounts.csv` exports populated `institution_id` values for accounts with an institution.
- A test proves `account_tags.csv` is written with one row per persisted account-tag association.
- A test proves `account_tags.csv` uses `account_id,tag_id` rather than denormalized tag lists.
- A regression test proves the previously exported legacy tables still export successfully.
- A regression test proves empty institution, tag, or account-tag tables do not crash export.
- A regression test proves export output ordering is deterministic enough for stable tests.

## Manual

1. Populate a local database with institutions, tags, tagged accounts, balances, and exchange rates.
2. Run `nwtrack export tables-csv --interactive` and confirm the generated directory includes all expected CSV files.
3. Confirm `institutions.csv` contains the expected institution rows and headers.
4. Confirm `tags.csv` contains the expected tag rows and headers.
5. Confirm `accounts.csv` includes the `institution_id` column and preserves blank values for accounts without an institution.
6. Confirm `account_tags.csv` contains one row per stored account-tag link.
7. Run the non-interactive export path and confirm it produces the same table set.
8. Confirm the previously exported files for currencies, categories, balances, and exchange rates are still present and readable.
9. Confirm the richer default export output is understandable as a normalized backup bundle without needing additional metadata files.

## Tone Check

- The spec uses precise CLI-first language rather than abstract serialization terminology alone.
- The CSV contract is described concretely enough for implementation and tests to share the same expectations.
- The compatibility change is explicit rather than hidden behind vague wording.
- The relationship model stays normalized and conservative instead of introducing presentation-oriented shortcuts.

## Definition Of Done

- The Phase 21 spec directory exists with the three required documents.
- The spec clearly defines the richer default CSV export contract for institutions, tags, and account-tag relationships.
- The spec preserves the existing export command path while allowing the output contract to evolve.
- The spec gives Phase 22 a stable export contract to target for later import and round-trip work.
- The spec names the automated tests, manual checks, and quality gates needed to validate the feature.
