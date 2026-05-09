# Phase 10 Validation: Institution Schema Foundation

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Institution Persistence Baseline
- [X] Account Schema Integration
- [X] Repository And Unit Of Work Support
- [X] Compatibility Boundaries
- [X] Validation

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260509-institution-schema-foundation/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document states that Phase 10 adds first-class institution persistence in a schema-first slice.
- The requirements document defines `Institution` with fields `id`, `name`, and optional `description`.
- The requirements document states that institution names are unique.
- The requirements document states that accounts gain an optional `institution_id` reference to `institutions.id`.
- The requirements document states that existing accounts remain valid without an institution.
- The requirements document requires first-class repository support through `InstitutionsRepository` and `uow.institutions`.
- The requirements document states that CLI CRUD, account workflow changes, reporting changes, and fetch-service changes are deferred.
- The requirements document states that CSV import/export behavior remains unchanged in Phase 10.
- The requirements document states that delete semantics for referenced institutions are explicitly deferred to Phase 11.

Feature-specific implementation tests required by this phase:

- A schema test proves the `institutions` table is created successfully with the updated metadata.
- A repository test proves an institution can be inserted and fetched by id.
- A repository test proves an institution can be fetched by unique name.
- A repository test proves institutions can be listed and counted.
- A repository test proves repository hydration works for institution records.
- A persistence test proves an account can be stored and read with `institution_id` unset.
- A persistence test proves an account can be stored and read with a valid linked institution.
- A compatibility test proves existing CSV-backed database initialization still succeeds without an institutions CSV file.
- Existing account and balance tests continue to pass after the schema extension.

## Manual

1. Read `requirements.md` and confirm the phase is limited to persistence and schema foundations rather than CLI behavior.
2. Confirm the institution section keeps the entity shape limited to `id`, `name`, and optional `description`.
3. Confirm the account relationship section keeps institution assignment optional in Phase 10.
4. Confirm the persistence section requires first-class repository and unit-of-work support for institutions.
5. Confirm the compatibility section preserves current CSV contracts rather than extending them in this phase.
6. Confirm the deferred section leaves delete semantics for referenced institutions to Phase 11.
7. Initialize a fresh database and confirm schema creation succeeds with the new institution table present.
8. Confirm existing account flows still work without requiring institution-aware prompts or commands.
9. Confirm no new CSV file is required by the existing initialization workflow.
10. Confirm no export contract is changed in this phase.

## Tone Check

- The spec uses precise persistence-oriented language rather than prematurely describing future CLI behavior.
- The phase remains conservative, compatibility-preserving, and independently shippable.
- Deferrals are explicit where later phases still need to make product decisions.
- Validation describes concrete schema and compatibility proofs, not only generic repository commands.

## Definition Of Done

- The Phase 10 spec directory exists with the three required documents.
- The spec aligns with `specs/mission.md`, `specs/roadmap.md`, and `specs/tech-stack.md`.
- The spec defines institution persistence, optional account linkage, and repository/unit-of-work exposure clearly enough for implementation.
- The spec preserves current account and CSV workflows by deferring CLI and CSV changes explicitly.
- The spec names the automated tests, manual checks, and quality gates needed to prove schema safety and compatibility.
