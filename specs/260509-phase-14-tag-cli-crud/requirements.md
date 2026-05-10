# Phase 14 Requirements: Tag CLI CRUD

## Scope

This phase makes tags independently manageable from the CLI without yet threading tag selection through account workflows.

Included in this phase:

- Add interactive CLI commands to list, create, update, and delete tags
- Add tag presenter ports and Rich presenter adapters for those workflows
- Add tag use cases and CLI wiring that match the existing institution administration pattern
- Add shared internal helpers for tag administration that later account workflows can reuse
- Surface linked-account usage counts in tag administration views
- Normalize tag names before validation and persistence by trimming whitespace, collapsing repeated whitespace, and lowercasing
- Define and validate delete protection when accounts still reference a tag

Not included in this phase:

- Account create, update, list, or detail workflow changes for tags
- Tag-aware account presentation changes
- Fetch-service additions for tag reads unless strictly required by the CRUD workflows
- CSV import or export contract changes
- Reporting changes or tag-aware report output
- Reassignment, detach-on-delete, or force-delete flows for linked tags

### Tag CLI Surface

This phase adds a first-class CLI command group for tag administration.

Required commands:

- `tags list`
- `tags create`
- `tags update`
- `tags delete`

CLI expectations for this phase:

- Commands remain interactive and presenter-driven.
- Workflows should follow the same overall shape as the current institution administration flows.
- Tag selection for update and delete is by numeric tag ID after showing a tag table.
- List and selection views should show linked-account counts so delete safety is visible before the user confirms an action.

### Tag Fields In Scope

This phase uses the Phase 13 tag shape without adding new fields.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `int` | Primary key, unique | Internal identifier |
| `name` | `string` | Required, unique after normalization | Canonical stored tag label |
| `description` | `string` | Optional free-text | Supplemental context only |

### Tag Name Normalization

This phase defines canonical tag-name storage behavior for CLI CRUD.

- User input must be normalized before duplicate checks, preview, and persistence.
- Normalization trims leading and trailing whitespace.
- Normalization collapses repeated internal whitespace to single spaces.
- Normalization lowercases the final stored value.
- A name that becomes empty after normalization must be rejected.
- Duplicate validation is performed against normalized values so visually different whitespace or casing does not create separate tags.

Examples:

- `"  Emergency Fund  "` becomes `"emergency fund"`
- `"Long   Term   Hold"` becomes `"long term hold"`
- `"LIQUID"` becomes `"liquid"`

### Workflow Behavior

#### List

- `tags list` displays all tags ordered by ascending ID.
- The displayed table should include `ID`, `Name`, `Description`, and `Accounts`.
- The `Accounts` column shows the number of accounts currently referencing each tag.
- Empty-state behavior must be explicit and readable when no tags exist.

#### Create

- `tags create` shows the current tag list before collecting input.
- The workflow collects `name` and optional `description`.
- The workflow normalizes the entered name before validation and persistence.
- The workflow previews the normalized tag, asks for confirmation, inserts the record, validates the result, and then shows the refreshed list.
- Duplicate names must be rejected before insert using normalized-value validation, while still preserving the database uniqueness constraint as the last line of defense.

#### Update

- `tags update` shows the current tag list and prompts for tag ID.
- If no tags exist, the workflow exits cleanly with a clear message.
- If the chosen ID does not exist, the workflow shows a validation message and re-prompts.
- The workflow loads current values as defaults for `name` and `description`.
- The workflow normalizes the entered name before validation and persistence.
- The workflow previews the normalized updated record, asks for confirmation, updates the record, validates the result, and then shows the refreshed list.
- Updating a tag may change `name` and `description` only; `id` remains fixed.
- A new name that duplicates another tag after normalization must be rejected before update.

#### Delete

- `tags delete` shows the current tag list and prompts for tag ID.
- If no tags exist, the workflow exits cleanly with a clear message.
- If the chosen ID does not exist, the workflow shows a validation message and re-prompts.
- The workflow previews the selected tag and its linked-account count before confirmation.
- Deletion is allowed only when the linked-account count is zero.
- If any account still references the tag, deletion is blocked with a clear validation-style message that includes the linked-account count.
- This phase does not detach account-tag links automatically, cascade-delete linked accounts, or offer a force-delete path.

## Decisions

### Decisions Locked In For This Phase

- Phase 14 is limited to interactive tag CRUD on top of the Phase 13 persistence layer.
- Tag administration uses a dedicated `tags` CLI command group.
- Update and delete select tags by numeric ID.
- Tag list and selection views surface linked-account usage counts.
- Delete is restricted when any account still references the tag.
- CLI behavior remains presenter-driven and should follow existing institution administration patterns.
- Tag names are stored in canonical normalized form by trimming whitespace, collapsing repeated whitespace, and lowercasing.
- Shared internal helper code for tag list rows and related admin support is included now so later account workflows can reuse it.
- Fetch-service tag methods remain deferred to a later phase unless a narrow CRUD need emerges during implementation.
- CSV import/export behavior remains unchanged in this phase.

### Decisions Explicitly Deferred

- Tag selection during account creation or account updates
- Tag display in account list and account detail outputs
- Fetch-service methods for tag reads outside these CLI workflows
- CSV file shape for tag or account-tag import/export
- Reporting behavior that groups or displays by tag
- Aggregation semantics for multi-tag accounts
- Reassignment or detach flows for deleting a referenced tag

## Context

This spec should be interpreted through `specs/mission.md`, `specs/roadmap.md`, `specs/tech-stack.md`, and the Phase 13 tag schema spec.

Implementation context for this phase:

- Phase 13 already established first-class tag persistence, many-to-many account linkage, and `uow.tags`.
- Existing institution CRUD is the nearest implementation pattern for command structure, presenter boundaries, preview/confirm behavior, and success/error messaging.
- The product remains CLI-first and local-first, so the workflows should favor readable tables, clear prompts, and explicit validation over hidden behavior.
- This phase should stay independently shippable without broad account workflow rewiring.

Tone and implementation expectations:

- Use precise CLI-oriented language.
- Prefer compatibility-preserving behavior over shortcuts.
- Make delete safety obvious before the user confirms an action.
- Keep normalization behavior explicit so storage and duplicate checks cannot drift.
- Keep the phase narrow enough that Phase 15 can cleanly own account workflow integration.
