# Phase 11 Requirements: Institution CLI CRUD

## Scope

This phase makes institutions user-manageable from the CLI without yet threading institution selection through account workflows.

Included in this phase:

- Add interactive CLI commands to list, create, update, and delete institutions
- Add institution presenter ports and Rich presenter adapters for those workflows
- Add institution use cases and CLI wiring that match existing category and account administration patterns
- Extend institution repository support as needed for update, delete, and linked-account validation
- Surface linked-account usage counts in institution administration views
- Define and validate delete protection when accounts still reference an institution

Not included in this phase:

- Account create, update, list, or detail workflow changes
- Fetch-service additions for institution reads
- CSV import or export contract changes
- Reporting changes or institution-aware report output
- Reassignment flows for linked accounts during deletion
- The later transition to institution-required accounts

### Institution CLI Surface

This phase adds a first-class CLI command group for institution administration.

Required commands:

- `institutions list`
- `institutions create`
- `institutions update`
- `institutions delete`

CLI expectations for this phase:

- Commands remain interactive and presenter-driven.
- Workflows should follow the same overall shape as the current category and account administration flows.
- Institution selection for update and delete is by numeric institution ID after showing an institution table.
- List and selection views should show institution usage counts so delete safety is visible before the user confirms an action.

### Institution Fields In Scope

This phase uses the Phase 10 institution shape without adding new fields.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `int` | Primary key, unique | Internal identifier |
| `name` | `string` | Required, unique | Primary user-facing institution label |
| `description` | `string` | Optional free-text | Supplemental context only |

### Workflow Behavior

#### List

- `institutions list` displays all institutions ordered by ascending ID.
- The displayed table should include `ID`, `Name`, `Description`, and `Accounts`.
- The `Accounts` column shows the number of accounts currently referencing each institution.
- Empty-state behavior must be explicit and readable when no institutions exist.

#### Create

- `institutions create` shows the current institution list before collecting input.
- The workflow collects `name` and optional `description`.
- The workflow previews the new institution, asks for confirmation, inserts the record, validates the result, and then shows the refreshed list.
- Duplicate names must be rejected before insert using case-insensitive validation, while still preserving the database uniqueness constraint as the last line of defense.

#### Update

- `institutions update` shows the current institution list and prompts for institution ID.
- If no institutions exist, the workflow exits cleanly with a clear message.
- If the chosen ID does not exist, the workflow shows a validation message and re-prompts.
- The workflow loads current values as defaults for `name` and `description`.
- The workflow previews the updated record, asks for confirmation, updates the record, validates the result, and then shows the refreshed list.
- Updating an institution may change `name` and `description` only; `id` remains fixed.
- A new name that duplicates another institution must be rejected case-insensitively before update.

#### Delete

- `institutions delete` shows the current institution list and prompts for institution ID.
- If no institutions exist, the workflow exits cleanly with a clear message.
- If the chosen ID does not exist, the workflow shows a validation message and re-prompts.
- The workflow previews the selected institution and its linked-account count before confirmation.
- Deletion is allowed only when the linked-account count is zero.
- If any account still references the institution, deletion is blocked with a clear validation-style message that includes the linked-account count.
- This phase does not null out account references, cascade delete linked accounts, or prompt the user to reassign accounts.

## Decisions

### Decisions Locked In For This Phase

- Phase 11 is limited to interactive institution CRUD on top of the Phase 10 persistence layer.
- Institution administration uses a dedicated `institutions` CLI command group.
- Update and delete select institutions by numeric ID.
- Institution list and selection views surface linked-account usage counts.
- Delete is restricted when any account still references the institution.
- CLI behavior remains presenter-driven and should follow existing category/account administration patterns.
- Institution names remain unique and are validated case-insensitively in the interactive workflows.
- Fetch-service institution methods remain deferred to a later phase.
- CSV import/export behavior remains unchanged in this phase.

### Decisions Explicitly Deferred

- Institution selection during account creation or account updates
- Institution display in account list and account detail outputs
- Institution-specific fetch-service methods
- CSV file shape for institution import/export
- Reassignment flows for deleting a referenced institution
- Reporting behavior that groups or displays by institution
- The later cutover to institution-required accounts

## Context

This spec should be interpreted through `specs/mission.md`, `specs/roadmap.md`, `specs/tech-stack.md`, and the Phase 10 institution schema spec.

Implementation context for this phase:

- Phase 10 already established first-class institution persistence, optional `Account.institution_id`, and `uow.institutions`.
- Existing interactive admin flows for categories and accounts are the pattern to follow for command structure, presenter boundaries, preview/confirm behavior, and success/error messaging.
- The product remains CLI-first and local-first, so the workflows should favor readable tables, clear prompts, and explicit validation over hidden behavior.
- This phase should stay independently shippable without broad account workflow rewiring.

Tone and implementation expectations:

- Use precise CLI-oriented language.
- Prefer compatibility-preserving behavior over clever shortcuts.
- Make delete safety obvious before the user confirms an action.
- Keep the phase narrow enough that Phase 12 can cleanly own account workflow integration.
