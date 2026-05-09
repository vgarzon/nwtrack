# Phase 12b Requirements: Interactive Balance Creation

## Scope

This phase adds a narrow interactive workflow for creating one missing balance entry without changing the existing balance update, delete, roll-forward, or transfer workflows.

Included in this phase:

- Add an interactive `balances create` CLI command
- Show the active-accounts table before prompting for account selection
- Select the target account by numeric account ID
- Collect one `YYYY-MM` month and one amount for the new balance row
- Show a preview and require confirmation before insert
- Reject duplicate `(account_id, month)` balance entries with clear validation
- Show a success message and created-balance preview after insert

Not included in this phase:

- Schema changes or migration work
- Batch or looped creation of multiple balances in one run
- Changes to `balances update`
- Changes to `balances delete`
- Changes to `balances roll`
- Changes to `balances transfer`
- Reporting, export, or CSV contract changes
- Tag work

### Balance Create Workflow Surface

This phase adds one new command to the existing balance command group.

Command in scope:

- `balances create`

CLI expectations for this phase:

- The workflow remains interactive and presenter-driven.
- The command creates exactly one balance row per invocation.
- The workflow shows the active accounts table before account selection.
- Account selection is by account ID rather than by table index.
- The workflow accepts any valid `YYYY-MM` month value.
- The workflow requires explicit confirmation before insert.
- Existing balance commands remain unchanged during this phase.

### Balance Data In Scope

This phase uses the existing monthly balance model and does not change its storage shape.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `int` | Primary key, unique | Existing internal identifier |
| `account_id` | `int` | Required, foreign key | Selected from active accounts in this phase |
| `month` | `Month` | Required, valid `YYYY-MM` | Any valid month is allowed |
| `amount` | `int` | Required | Uses the current balance amount conventions |

### Workflow Behavior

#### Create

- `balances create` shows the active accounts table before collecting workflow input.
- The workflow collects account ID first, then month, then amount.
- The workflow shows a preview of the balance to be created before confirmation.
- If the user cancels at any point before confirmation, no balance row is created.
- If the selected `account_id` and `month` already exist, the workflow must reject the create request without modifying the existing balance.
- Duplicate rejection must explicitly direct the user to `balances update`.
- On success, the workflow shows a success message and a preview of the created row.

#### Account Eligibility

- This phase limits `balances create` to active accounts only.
- If there are no eligible active accounts, the workflow exits cleanly without insert.
- Inactive-account handling remains unchanged outside this new command.

#### Month And Amount Rules

- The workflow accepts any valid `YYYY-MM` month rather than limiting creation to existing months.
- Amount entry reuses the current balance amount semantics rather than introducing new signed-entry rules in this phase.

## Decisions

### Decisions Locked In For This Phase

- Phase 12b is limited to one-off interactive balance creation.
- The workflow collects data in the order: account ID, month, amount.
- Account selection uses account ID rather than indexed account rows.
- The workflow targets active accounts only.
- Any valid `YYYY-MM` month is allowed.
- A final preview and confirmation step are required before insert.
- Duplicate balance rows are rejected rather than overwritten.
- Duplicate messaging explicitly directs the user to `balances update`.
- Success output shows both a success message and the created-balance preview.
- Existing balance update, delete, roll-forward, and transfer workflows remain unchanged.

### Decisions Explicitly Deferred

- Batch creation of multiple balances in one run
- Month-bootstrap workflows for creating several rows together
- Inactive-account support in `balances create`
- Any redesign of the broader balance command surface
- New amount-entry semantics
- Reporting or export behavior tied to this command

## Context

This spec should be interpreted through `specs/mission.md`, `specs/roadmap.md`, and `specs/tech-stack.md`.

Implementation context for this phase:

- The current balance command group already includes `roll`, `update`, `delete`, and `transfer`.
- Existing balance workflows already use active-account-oriented selection and presenter-driven terminal interaction.
- Existing storage already enforces uniqueness at `(account_id, month)`, so this phase is a workflow addition rather than a schema phase.

Tone and implementation expectations:

- Keep the command narrow and independently shippable.
- Favor low-friction monthly entry without collapsing create into update behavior.
- Use explicit validation and readable terminal output rather than implicit fallback behavior.
- Preserve compatibility in the rest of the balance CLI surface during this phase.
