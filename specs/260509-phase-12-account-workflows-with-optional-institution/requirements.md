# Phase 12 Requirements: Account Workflows With Optional Institution

## Scope

This phase threads optional institution support through account creation, account updates, and account listing without yet changing balance workflows, reporting, or CSV contracts.

Included in this phase:

- Add optional institution assignment to interactive account creation
- Add optional institution assignment, reassignment, and clearing to interactive account updates
- Surface institution consistently in account list output and account create/update previews
- Extend account-facing fetch/read support only as needed for institution-aware account workflows in this phase
- Preserve compatibility for accounts that still have no institution assigned

Not included in this phase:

- Institution-required validation or migration rules
- Balance workflow changes
- Reporting changes or institution-aware report output
- CSV import or export contract changes
- Tag work
- Broader account detail or read-model redesign beyond what this phase needs

### Account Workflow Surface

This phase updates the existing account command surface rather than adding new commands.

Commands in scope:

- `accounts create`
- `accounts update`
- `accounts list`

CLI expectations for this phase:

- The workflows remain interactive and presenter-driven.
- Institution selection follows the same indexed-choice pattern already used for categories and currencies.
- The institution field is optional and must always provide an explicit no-institution path.
- Existing accounts without an institution remain fully valid.

### Institution Selection Behavior

Institution selection in this phase uses a numbered table plus an explicit no-institution option.

Required behavior:

- Create and update show a readable indexed institutions table when institutions exist.
- The prompt includes an explicit `None` / no-institution choice.
- Update uses the current institution as the default when one is assigned.
- Update uses the no-institution option as the default when no institution is assigned.
- If no institutions exist, create and update continue without failure and make it clear that no institution is available.

This phase does not use institution ID entry or free-text institution name entry for account workflows.

### Account Data In Scope

This phase uses the existing account shape and extends account workflow input/output to include optional institution assignment.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `int` | Primary key, unique | Existing internal identifier |
| `name` | `string` | Required, unique | Existing account label |
| `description` | `string` | Existing behavior | Existing optional/free-text semantics remain unchanged |
| `category_name` | `string` | Required | Existing category association |
| `currency_code` | `string` | Required | Existing currency association |
| `status` | `enum` | Required | Existing active/inactive behavior |
| `institution_id` | `int \| None` | Optional foreign key | New workflow-visible field for this phase |

### Workflow Behavior

#### Create

- `accounts create` continues to show existing accounts before collecting input.
- The workflow collects institution selection after the existing classification inputs and before confirmation.
- The user may choose an institution or explicitly choose no institution.
- If no institutions exist, the workflow informs the user and continues with no institution assigned.
- The create preview must show institution consistently, including the unassigned case.
- The stored account must preserve the selected `institution_id` or `None`.

#### Update

- `accounts update` continues to show accounts and select the target account by account ID.
- The workflow must allow the user to keep the current institution, change it to another institution, or clear it.
- The institution selection step follows the same indexed-choice pattern as create.
- If no institutions exist, the workflow must still allow the account to remain unassigned.
- The update preview must show institution consistently, including the unassigned case.
- The stored account must preserve the chosen `institution_id` or `None`.

#### List

- `accounts list` surfaces institution in the account table.
- The institution display must be consistent for assigned and unassigned accounts.
- This phase uses `None` as the display label for an unassigned institution.
- Existing list behavior remains unchanged otherwise, including support for active-only filtering.

## Decisions

### Decisions Locked In For This Phase

- Phase 12 is limited to account create, update, and list workflows.
- Institution selection in account workflows uses indexed selection, not institution ID entry.
- Account workflows must include an explicit no-institution option.
- Fetch-service expansion stays minimal and only supports this phase's account workflows.
- Existing accounts without an institution remain valid and usable throughout this phase.
- Institution display is added to account list and account create/update previews in this phase.

### Decisions Explicitly Deferred

- Making institution assignment mandatory
- Broader account detail/read-model redesign
- Institution-aware balance workflows
- Institution-aware reporting behavior
- CSV import/export changes
- Tag schema and tag assignment behavior
- Migration/cutover rules for requiring institutions later

## Context

This spec should be interpreted through `specs/mission.md`, `specs/roadmap.md`, `specs/tech-stack.md`, and the earlier institution phases.

Implementation context for this phase:

- Phase 10 already established optional `Account.institution_id` in persistence.
- Phase 11 established first-class institution CLI administration and readable institution tables.
- Current account creation and update workflows already use presenter-driven indexed selection for categories and currencies; institution selection should follow that same interaction model.
- Current account listing already uses a dedicated Rich table, so institution display should be added there rather than introduced as a separate detail view.

Tone and implementation expectations:

- Keep CLI ergonomics explicit and low-friction.
- Prefer readable tables and obvious defaults over compact but ambiguous prompts.
- Make the unassigned-institution state explicit without making it feel like an error.
- Keep the phase narrow and independently shippable so later phases can build on it cleanly.
