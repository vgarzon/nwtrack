# Phase 15 Requirements: Account Workflows With Tags

## Scope

This phase threads controlled tag assignment through account creation, account updates, and account listing without changing reporting, CSV contracts, or tag-administration behavior.

Included in this phase:

- Add optional zero-to-many tag assignment to interactive account creation
- Add optional zero-to-many tag assignment, replacement, and clearing to interactive account updates
- Surface tags consistently in account list output and account create/update previews
- Extend account-facing fetch/read support only as needed for tag-aware account workflows in this phase
- Keep tag-aware reads limited to listing selectable tags and loading assigned tags for account workflow defaults and presentation
- Preserve compatibility for accounts that still have zero tags assigned

Not included in this phase:

- New tag administration commands or changes to `tags list/create/update/delete`
- Reporting changes or tag-aware report output
- CSV import or export contract changes
- Aggregation semantics for multi-tag accounts in reports
- Broader account detail or read-model redesign beyond what this phase needs
- Institution-required migration or other non-tag account validation changes

### Account Workflow Surface

This phase updates the existing account command surface rather than adding new commands.

Commands in scope:

- `accounts create`
- `accounts update`
- `accounts list`

CLI expectations for this phase:

- The workflows remain interactive and presenter-driven.
- Institution selection remains the first collected field where it already exists.
- Tag selection is collected immediately after institution selection and before the other editable account fields.
- Tag selection follows the same indexed-choice style already used for category, currency, and institution selection.
- Tag assignment is optional and must always provide an explicit no-tags path.
- Existing accounts with zero tags remain fully valid.

### Tag Selection Behavior

Tag selection in this phase uses a numbered table plus an explicit no-tags option.

Required behavior:

- Create and update show a readable indexed tags table when tags exist.
- The prompt includes an explicit `0` option for no tags.
- The prompt accepts comma-separated indexes such as `1,3,4`.
- The prompt accepts `q` to quit the tag selector.
- Repeated indexes in one submission collapse to one selected tag.
- Invalid indexes are rejected with a clear validation message and a re-prompt.
- Entering `0` alone means no tags for create and clear all tags for update.
- Update pre-fills the current tag selection as the default and allows Enter to keep it unchanged.
- If no tags exist, create and update continue without failure and make it clear that no tags are available.

This phase does not use tag ID entry, free-text tag entry, or one-by-one repeated tag prompts for account workflows.

### Account Data In Scope

This phase uses the existing account shape and extends account workflow input/output to include optional zero-to-many tags.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `int` | Primary key, unique | Existing internal identifier |
| `name` | `string` | Required, unique | Existing account label |
| `description` | `string` | Existing behavior | Existing optional/free-text semantics remain unchanged |
| `category_name` | `string` | Required | Existing category association |
| `currency_code` | `string` | Required | Existing currency association |
| `status` | `enum` | Required | Existing active/inactive behavior |
| `institution_id` | `int \| None` | Optional foreign key | Existing workflow-visible field from Phase 12 |
| `tag_ids` | `list[int]` | Optional, zero-to-many | Workflow input used to replace account-tag links |
| `tags` | `list[string]` | Derived, zero-to-many | Displayed alphabetically by normalized stored name |

### Tag Display Behavior

- `accounts list` adds a `Tags` column immediately after `Name`.
- The tags column displays a comma-separated alphabetical list of assigned tag names.
- Accounts with zero tags display a blank cell in account tables.
- Create and update previews display tags using the same alphabetical comma-separated rendering.
- Preview output uses `None` for the no-tags state so the empty assignment is explicit before confirmation.

### Workflow Behavior

#### Create

- `accounts create` continues to show existing accounts before collecting input.
- The workflow collects institution first, then tag selection, then the remaining account fields.
- The user may choose zero, one, or many tags.
- If no tags exist, the workflow informs the user and continues with no tags assigned.
- The create preview must show tags consistently, including the no-tags case.
- The stored account must preserve the selected `institution_id` and selected tag associations.

#### Update

- `accounts update` continues to show accounts and select the target account by account ID.
- The workflow must allow the user to keep the current tag set, replace it with a different tag set, or clear all tags.
- The tag selection step is the second editable field, immediately after institution selection.
- The current tag set is the default selection for update.
- If no tags exist, the workflow must still allow the account to remain with zero tags.
- The update preview must show tags consistently, including the no-tags case.
- The stored account must preserve the chosen `institution_id` and chosen tag associations.

#### List

- `accounts list` surfaces tags in the account table.
- The `Tags` column appears immediately after `Name`.
- The tag display must be consistent for zero-tag, single-tag, and multi-tag accounts.
- Existing list behavior remains unchanged otherwise, including support for active-only filtering.

## Decisions

### Decisions Locked In For This Phase

- Phase 15 is limited to account create, update, and list workflows.
- Account workflows use indexed multi-select for tag assignment, not tag IDs.
- Tag selection accepts comma-separated indexes in one prompt.
- `0` is the explicit no-tags choice and `q` quits the tag selector.
- Update defaults to the current tag set and allows Enter to keep it unchanged.
- Submitted tag selections replace the full tag set for the account.
- Multi-tag display uses a comma-separated alphabetical list of stored tag names.
- Account list output and create/update previews surface tags in this phase.
- Fetch/read expansion stays minimal and only supports this phase's account workflows.
- Existing accounts with zero tags remain valid and usable throughout this phase.

### Decisions Explicitly Deferred

- Reporting behavior that groups or displays by tag
- Aggregation semantics for multi-tag accounts in reports
- CSV file shape for tag or account-tag import/export
- Tag-aware balance workflows
- Broader account detail/read-model redesign
- Any changes to tag CRUD or tag normalization rules beyond existing behavior

## Context

This spec should be interpreted through `specs/mission.md`, `specs/roadmap.md`, `specs/tech-stack.md`, and the earlier institution and tag phases.

Implementation context for this phase:

- Phase 12 already established the account-workflow pattern for extending create, update, and list with one additional account attribute.
- Phase 13 established many-to-many account-to-tag persistence.
- Phase 14 established controlled tag administration, canonical tag-name normalization, and repository support for replacing account-tag links.
- Current account creation and update workflows already use presenter-driven indexed selection for account-editable fields; tag selection should follow that same interaction model.
- Current account listing already uses a dedicated Rich table, so tag display should be added there rather than introduced as a separate detail flow.

Tone and implementation expectations:

- Keep CLI ergonomics explicit and low-friction.
- Prefer readable tables and obvious defaults over compact but ambiguous prompts.
- Make the zero-tags state feel normal and supported, not like an error path.
- Keep the phase narrow and independently shippable so later aggregation/reporting phases can build on it cleanly.
