# Phase 13 Validation: Tag Schema Foundation

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [ ] Tag Persistence Baseline
- [ ] Account-Tag Association Integration
- [ ] Repository And Unit Of Work Support
- [ ] Compatibility Boundaries
- [ ] Validation

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260509-phase-13-tag-schema-foundation/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document states that Phase 13 adds first-class tag persistence in a schema-first slice.
- The requirements document defines `Tag` with fields `id`, `name`, and optional `description`.
- The requirements document states that tag names are unique.
- The requirements document states that accounts gain many-to-many tag support through `account_tags`.
- The requirements document states that the `account_tags` table enforces uniqueness on `(account_id, tag_id)`.
- The requirements document states that existing accounts remain valid without tags.
- The requirements document requires first-class repository support through `TagsRepository` and `uow.tags`.
- The requirements document states that CSV import/export behavior remains unchanged in Phase 13.
- The requirements document states that CLI CRUD, account workflow changes, fetch-service changes, reporting changes, and multi-tag aggregation semantics are deferred.
- The requirements document states that deleting an account or tag cleans up only related association rows at the database level.

Feature-specific implementation tests required by this phase:

- A schema test proves the `tags` table is created successfully with the updated metadata.
- A schema test proves the `account_tags` table is created successfully with the expected unique constraint.
- A repository test proves a tag can be inserted and fetched by id.
- A repository test proves a tag can be fetched by unique name.
- A repository test proves tags can be listed, counted, updated, and deleted.
- A repository test proves repository hydration works for tag records.
- A repository test proves linked-account counts are reported correctly for a tag.
- A persistence test proves an account can be stored and read with zero tags.
- A persistence test proves one account can hold multiple tags.
- A persistence test proves one tag can be shared across multiple accounts.
- A repository test proves `replace_for_account` can attach, replace, and clear tag associations.
- A persistence test proves duplicate `(account_id, tag_id)` associations are rejected.
- A persistence test proves deleting an account removes only related `account_tags` rows.
- A persistence test proves deleting a tag removes only related `account_tags` rows.
- A compatibility test proves existing SQLite database files without tag tables are upgraded in place by the schema ensure path.
- A compatibility test proves existing CSV-backed database initialization still succeeds without tags or account-tags CSV files.
- Existing account, balance, and institution tests continue to pass after the schema extension.

## Manual

1. Read `requirements.md` and confirm the phase is limited to persistence and schema foundations rather than CLI behavior.
2. Confirm the tag section keeps the entity shape limited to `id`, `name`, and optional `description`.
3. Confirm the account relationship section keeps tag assignment optional in Phase 13.
4. Confirm the persistence section requires first-class repository and unit-of-work support for tags.
5. Confirm the compatibility section preserves current CSV contracts rather than extending them in this phase.
6. Confirm the deferred section leaves CLI-visible tag delete and rename behavior to Phase 14.
7. Initialize a fresh database and confirm schema creation succeeds with both the `tags` and `account_tags` tables present.
8. Confirm existing account flows still work without requiring tag-aware prompts or commands.
9. Confirm no new CSV file is required by the existing initialization workflow.
10. Confirm account-tag associations are cleaned up automatically when a linked account or tag is deleted, without deleting the other record type.

## Tone Check

- The spec uses precise persistence-oriented language rather than prematurely describing future CLI behavior.
- The phase remains conservative, compatibility-preserving, and independently shippable.
- Deferrals are explicit where later phases still need to make product decisions.
- Validation describes concrete schema, association, and compatibility proofs, not only generic repository commands.

## Definition Of Done

- The Phase 13 spec directory exists with the three required documents.
- The spec aligns with `specs/mission.md`, `specs/roadmap.md`, and `specs/tech-stack.md`.
- The spec defines tag persistence, many-to-many account linkage, and repository/unit-of-work exposure clearly enough for implementation.
- The spec preserves current account and CSV workflows by deferring CLI and CSV changes explicitly.
- The spec names the automated tests, manual checks, and quality gates needed to prove schema safety, association correctness, and compatibility.
