# Phase 10 Requirements: Institution Schema Foundation

## Scope

This phase adds first-class institution persistence in a conservative schema-first slice that keeps existing account workflows valid.

Included in this phase:

- Add `Institution` as first-class persisted reference data
- Add an optional `institution_id` reference from `Account` to `Institution`
- Extend ORM mappings, schema creation, repository protocols, SQLAlchemy repositories, and unit-of-work wiring to support institutions
- Preserve existing account and balance records without forced reassignment
- Define the validation needed to prove schema behavior and compatibility

Not included in this phase:

- CLI commands or prompts for institution management
- Account create, update, list, or detail workflow changes
- Fetch-service additions for institution-specific reads
- Reporting changes or institution-aware presentation
- CSV import or export contract changes
- Final delete semantics for referenced institutions
- The later cutover to institution-required accounts

### Institution

An institution is the financial institution where an account is held.

Institution baseline for this phase:

- `Institution` is first-class persisted reference data, not an unchecked account text field.
- The entity shape remains intentionally small: `id`, `name`, and optional `description`.
- Institution `name` must be unique so accounts can reference one unambiguous institution record.
- Additional institution attributes remain out of scope until a later phase explicitly adds them.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `int` | Primary key, unique | Internal identifier |
| `name` | `string` | Required, short label, unique | User-facing institution label |
| `description` | `string` | Optional free-text | Supplemental context only |

### Account Relationship

Account-to-institution behavior for this phase:

- An account may reference zero or one institution.
- The account persistence model adds an optional `institution_id` that references `institutions.id`.
- Existing accounts must remain valid when `institution_id` is absent.
- This phase must not force any institution assignment during schema initialization, upgrade, or normal use.
- Account-facing workflows remain unchanged until Phase 12 wires institutions into creation, editing, and listing flows.

### Persistence And Unit Of Work

Persistence scope for this phase:

- Add an `Institution` ORM mapping and backing table.
- Add repository protocol support through a first-class `InstitutionsRepository`.
- Add SQLAlchemy repository support and expose it on `UnitOfWork` as `uow.institutions`.
- Support enough repository behavior now to unblock later CLI work without requiring another persistence-only phase.

Required repository surface for Phase 10:

- `insert`
- `get_by_id`
- `get_by_name`
- `get_all`
- `count`
- `delete_all`
- `hydrate`
- `hydrate_many`

This phase does not require institution-specific use cases, presenters, or fetch-service methods.

### Schema And Compatibility Posture

Schema and compatibility expectations for this phase:

- The schema creation path remains the current SQLAlchemy metadata-driven approach used by the project.
- The implementation must preserve existing account and balance records.
- No bulk backfill or automatic institution assignment is required.
- Existing initialization and export flows remain compatible by keeping their current CSV contract unchanged in this phase.
- The absence of institution CSV support in Phase 10 is intentional and must be documented as a deferral, not treated as an omission.

### Delete Semantics Deferred

This phase intentionally does not finalize the product rule for deleting institutions that are referenced by accounts.

- Phase 10 should define institution persistence without depending on a final user-facing delete policy.
- Phase 11 should decide the CLI-visible validation and error behavior for deletion.
- Phase 10 must not claim automatic nulling, cascade deletion, or restricted deletion as a settled product rule.

## Decisions

### Decisions Locked In For This Phase

- Phase 10 is a narrow schema-first slice rather than a CLI or workflow phase.
- `Institution` becomes first-class persisted reference data now.
- Accounts gain an optional `institution_id` reference now.
- `Institution` uses the Phase 9 baseline shape: `id`, `name`, and optional `description`.
- Institution names remain unique.
- Repository and unit-of-work support for institutions are included now instead of being deferred to Phase 11.
- Existing accounts remain valid without institutions.
- CSV import and export behavior remain unchanged in this phase and are explicitly deferred.
- Delete semantics for referenced institutions are deferred to Phase 11.

### Decisions Explicitly Deferred

- Institution CRUD command shape and prompt flows
- Account workflow changes to capture or display institutions
- Fetch-service methods for institution reads
- CSV file shape for institution import/export
- Reporting behavior that groups or displays by institution
- The migration path for making institutions mandatory later
- User-facing delete restrictions or remediation flows

## Context

This spec should be interpreted through the project constitution in `specs/mission.md`, `specs/roadmap.md`, and `specs/tech-stack.md`.

Implementation context for this phase:

- `nwtrack` remains CLI-first, local-first, and SQLite-backed.
- The current schema path is SQLAlchemy metadata table creation, not Alembic-managed migrations.
- The existing export and CSV-init paths use fixed repository/table lists, so Phase 10 should preserve that behavior by deferring institution CSV support explicitly.
- New persistence work should follow existing layered boundaries: domain and ORM model shape, repository protocol, SQLAlchemy repository, and unit-of-work composition.

Tone and implementation expectations:

- Prefer compatibility-preserving behavior over broad rewiring.
- Keep the phase independently shippable even though institutions are not yet user-manageable.
- Use precise persistence-oriented language and avoid promising later CLI behavior too early.
- Call out deferrals explicitly when later phases still need to decide behavior.
