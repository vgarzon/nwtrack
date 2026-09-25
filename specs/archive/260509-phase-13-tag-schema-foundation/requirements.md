# Phase 13 Requirements: Tag Schema Foundation

## Scope

This phase adds first-class tag persistence in a conservative schema-first slice that keeps existing account workflows valid.

Included in this phase:

- Add `Tag` as first-class persisted reference data
- Add an `account_tags` association table for many-to-many account tagging
- Extend ORM mappings, repository protocols, SQLAlchemy repositories, and unit-of-work wiring to support tags
- Preserve existing account and balance records without forced tag assignment
- Define the validation needed to prove schema behavior and compatibility

Not included in this phase:

- CLI commands or prompts for tag management
- Account create, update, list, or detail workflow changes for tags
- Fetch-service additions for tag-specific reads
- Reporting changes or tag-aware presentation
- CSV import or export contract changes
- Final CLI-visible delete or rename semantics for tag administration

### Tag

A tag is a reusable account label used for grouping and reporting.

Tag baseline for this phase:

- `Tag` is first-class persisted reference data, not an unchecked multi-value text field on accounts.
- The entity shape remains intentionally small: `id`, `name`, and optional `description`.
- Tag `name` must be unique so accounts can reference one unambiguous tag record.
- Additional tag attributes remain out of scope until a later phase explicitly adds them.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `int` | Primary key, unique | Internal identifier |
| `name` | `string` | Required, short label, unique | User-facing tag label |
| `description` | `string` | Optional free-text | Supplemental context only |

### Account Relationship

Account-to-tag behavior for this phase:

- An account may reference zero, one, or many tags.
- Tags may be shared across multiple accounts.
- The account persistence model adds an explicit `account_tags` association table rather than storing duplicated free-form tag text on accounts.
- Existing accounts must remain valid when no tag associations exist.
- This phase must not force any tag assignment during schema initialization, upgrade, or normal use.
- Account-facing workflows remain unchanged until Phase 15 wires tags into creation, editing, and listing flows.

### Persistence And Unit Of Work

Persistence scope for this phase:

- Add a `Tag` ORM mapping and backing table.
- Add an `account_tags` association table with:
  - `account_id` foreign key to `accounts.id`
  - `tag_id` foreign key to `tags.id`
  - composite unique constraint on `(account_id, tag_id)`
  - database-level `ON DELETE CASCADE` on both foreign keys so deleting an account or tag removes only its association rows
- Add repository protocol support through a first-class `TagsRepository`.
- Add SQLAlchemy repository support and expose it on `UnitOfWork` as `uow.tags`.
- Add ORM relationship support so account reads can surface tags in later phases without another schema-only change.
- Support enough repository behavior now to unblock later CLI and account-workflow phases without requiring another persistence-only phase.

Required repository surface for Phase 13:

- `insert`
- `get_by_id`
- `get_by_name`
- `get_all`
- `count`
- `delete_all`
- `update`
- `delete_by_id`
- `count_linked_accounts`
- `get_for_account`
- `replace_for_account`
- `hydrate`
- `hydrate_many`

This phase does not require tag-specific use cases, presenters, CLI commands, or fetch-service methods.

### Schema And Compatibility Posture

Schema and compatibility expectations for this phase:

- The schema creation path remains the current SQLAlchemy metadata-driven approach used by the project.
- The implementation must preserve existing account and balance records.
- Existing SQLite databases should gain missing `tags` and `account_tags` tables through the normal schema ensure path without any tag backfill logic.
- No bulk backfill or automatic tag assignment is required.
- Existing initialization and export flows remain compatible by keeping their current CSV contract unchanged in this phase.
- The absence of tag CSV support in Phase 13 is intentional and must be documented as a deferral, not treated as an omission.

### Delete Semantics Deferred

This phase intentionally does not finalize the product rule for CLI-visible tag deletion or rename behavior.

- Phase 13 should define tag persistence and association cleanup behavior without depending on a final interactive delete policy.
- Phase 14 should decide the CLI validation and error behavior for tag deletion and rename flows.
- Phase 13 does lock in database-level association cleanup so deleting an account or tag removes only related `account_tags` rows.
- Phase 13 must not claim final user-facing confirmation, remediation, or detach-first workflows as settled product rules.

## Decisions

### Decisions Locked In For This Phase

- Phase 13 is a narrow schema-first slice rather than a CLI or workflow phase.
- `Tag` becomes first-class persisted reference data now.
- Accounts gain many-to-many tag support now through `account_tags`.
- `Tag` uses the Phase 9 baseline shape: `id`, `name`, and optional `description`.
- Tag names remain unique.
- Repository and unit-of-work support for tags are included now instead of being deferred to Phase 14 or Phase 15.
- Existing accounts remain valid without tags.
- CSV import and export behavior remain unchanged in this phase and are explicitly deferred.
- Database-level association cleanup on account or tag deletion is included now through cascading foreign keys on `account_tags`.
- CLI-visible tag delete and rename behavior are deferred to Phase 14.

### Decisions Explicitly Deferred

- Tag CRUD command shape and prompt flows
- Account workflow changes to capture, edit, or display tags
- Fetch-service methods for tag reads
- CSV file shape for tag and account-tag import/export
- Reporting behavior that groups or displays by tag
- Aggregation semantics for multi-tag accounts
- User-facing delete restrictions, confirmations, or remediation flows

## Context

This spec should be interpreted through the project constitution in `specs/mission.md`, `specs/roadmap.md`, and `specs/tech-stack.md`.

Implementation context for this phase:

- `nwtrack` remains CLI-first, local-first, and SQLite-backed.
- The current schema path is SQLAlchemy metadata table creation, not Alembic-managed migrations.
- The existing export and CSV-init paths use fixed repository/table lists, so Phase 13 should preserve that behavior by deferring tag CSV support explicitly.
- New persistence work should follow existing layered boundaries: domain and ORM model shape, repository protocol, SQLAlchemy repository, and unit-of-work composition.
- Phase 10 provides the nearest implementation pattern: first establish persistence support, then layer CLI and workflow behavior in later phases.

Tone and implementation expectations:

- Prefer compatibility-preserving behavior over broad rewiring.
- Keep the phase independently shippable even though tags are not yet user-manageable.
- Use precise persistence-oriented language and avoid promising later CLI behavior too early.
- Call out deferrals explicitly when later phases still need to decide behavior.
