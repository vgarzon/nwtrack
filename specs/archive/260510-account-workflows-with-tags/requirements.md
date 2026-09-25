# Phase 15 Requirements: Account Workflows With Tags

## Scope

This phase threads tag assignment through account creation, account updates, account listing, and account create/update previews without changing reporting, CSV behavior, or the standalone tag administration workflows.

Included in this phase:

- Add zero-to-many tag assignment to interactive account creation
- Add zero-to-many tag replacement to interactive account updates
- Surface assigned tags in account list output and account create/update previews
- Extend account-facing fetch/read support only as needed for tag-aware account workflows in this phase
- Reuse the Phase 13 many-to-many account-tag model and the Phase 14 tag CRUD foundation
- Preserve compatibility for accounts that still have zero tags assigned

Not included in this phase:

- Tag CRUD command changes
- Reporting changes or tag-aware report output
- CSV import or export contract changes
- Balance workflow changes
- New account commands or a broader account detail redesign
- Incremental attach/detach tag editing separate from the main account update flow

### Account Workflow Surface

This phase updates the existing account command surface rather than adding new commands.

Commands in scope:

- `accounts create`
- `accounts update`
- `accounts list`

CLI expectations for this phase:

- The workflows remain interactive and presenter-driven.
- Tag selection follows the same readable table-plus-prompt style already used for institution, category, and currency selection.
- Tag selection uses displayed table indices, not raw tag IDs.
- Tag selection supports zero, one, or many tags.
- Existing accounts with zero tags remain fully valid.

### Tag Selection Behavior

Tag selection in this phase uses a numbered table plus one prompt that accepts comma-separated displayed indices.

Required behavior:

- Create and update show a readable indexed tags table when tags exist.
- Tag rows use displayed index values directly, starting at `1`.
- The prompt accepts comma-separated indices such as `1,3,4`.
- The prompt trims surrounding whitespace around comma-separated entries before validation.
- The prompt includes an explicit no-tags path using `0`.
- The prompt supports `q` to quit the workflow.
- Repeated selected indices are deduplicated before persistence.
- Invalid indices or malformed input are rejected with clear validation-style feedback and the workflow re-prompts.
- Selection order is normalized to the table order before preview and persistence so tag display stays deterministic.
- If no tags exist, create and update continue without failure and make it clear that no tags are available.

Update-specific behavior:

- Update uses the account's current assigned tags as the default selected set.
- Update edits tags as a full replacement step.
- Choosing `0` in update clears all existing tag assignments for the account.

This phase does not use free-text tag entry, tag-name search, raw tag-ID entry, or separate attach and detach sub-flows for account workflows.

### Account Data In Scope

This phase uses the existing account shape and extends account workflow input/output to include tag assignment and tag display.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `int` | Primary key, unique | Existing internal identifier |
| `name` | `string` | Required, unique | Existing account label |
| `description` | `string` | Existing behavior | Existing optional/free-text semantics remain unchanged |
| `category_name` | `string` | Required | Existing category association |
| `currency_code` | `string` | Required | Existing currency association |
| `status` | `enum` | Required | Existing active/inactive behavior |
| `institution_id` | `int \| None` | Existing optional foreign key | Continues unchanged from Phase 12 |
| `tag_ids` | `list[int]` | Zero, one, or many selected tags | New workflow input for create and update |
| `tags` | `list[Tag]` | Read-only workflow/display shape | Used for list output, previews, and account fetch/read models |

### Workflow Behavior

#### Create

- `accounts create` continues to show existing active accounts before collecting input.
- Institution selection remains the first collected field, as established in Phase 12.
- Tag selection is collected immediately after institution selection and before account name.
- The user may choose zero, one, or many tags.
- If no tags exist, the workflow informs the user and continues with no tags assigned.
- The create preview must show tags consistently, including the untagged case.
- The stored account must preserve the selected tag associations.
- Tag association persistence occurs as part of the account creation workflow and must not require a separate command.

#### Update

- `accounts update` continues to show accounts and select the target account by account ID.
- Institution remains the first editable field, as established in Phase 12.
- Tag replacement is the second editable step, immediately after institution selection.
- The workflow must allow the user to keep the current tag set, replace it with a different set, or clear it entirely.
- Current tag selections are used as the default value for the replacement prompt.
- If no tags exist, the workflow must still allow the account to remain or become untagged.
- The update preview must show tags consistently, including the untagged case.
- The stored account must preserve the chosen replacement tag set.

#### List

- `accounts list` surfaces tags in the account table.
- The `Tags` column appears after `Institution`.
- Assigned tags display as a comma-separated list of stored tag names.
- Untagged accounts display as blank cells in account tables.
- Existing list behavior remains unchanged otherwise, including support for active-only filtering.

#### Preview Behavior

- Account create and update previews must include a `Tags` field.
- Preview output uses a readable comma-separated tag list for tagged accounts.
- Preview output uses an explicit untagged label of `None` when no tags are assigned.
- Tag names in previews follow the same deterministic order used by the selection and persistence flow.

### Read And Fetch Support

This phase extends account-facing reads only as needed for the account workflows above.

Required read behavior:

- Account reads used by `accounts list`, `accounts create`, and `accounts update` expose assigned tags.
- Tag reads used for account workflow selection list all available tags in deterministic order.
- The fetch layer should grow only enough to support account workflow selection and account workflow presentation in this phase.

This phase does not introduce broader tag-fetch APIs for unrelated workflows.

## Decisions

### Decisions Locked In For This Phase

- Phase 15 is limited to account create, update, list, and preview behavior for tags.
- Tag selection in account workflows uses displayed indices, not tag IDs.
- Tag selection is multi-select and accepts comma-separated indices.
- The no-tags path is explicit and uses `0`.
- Account update edits tags as a full replacement step rather than incremental attach/detach prompts.
- Account list output gains a `Tags` column with comma-separated tag names.
- Account previews gain a `Tags` field and use `None` for the untagged case.
- Account table cells for untagged accounts remain blank, matching the current table convention for unassigned optional attributes.
- Read/fetch support expands only as needed for account workflows and account presentation in this phase.
- Existing accounts with zero tags remain valid and usable throughout this phase.

### Decisions Explicitly Deferred

- Tag-aware reporting behavior
- CSV import/export handling for account-tag data
- Tag search, fuzzy matching, or free-text tag entry in account workflows
- Dedicated account detail views beyond current list and preview surfaces
- Incremental attach-only or detach-only tag editing commands
- Any change to tag normalization rules established in Phase 14

## Context

This spec should be interpreted through `specs/mission.md`, `specs/roadmap.md`, `specs/tech-stack.md`, and the earlier tag and account workflow phases.

Implementation context for this phase:

- Phase 12 already established institution-aware account create, update, list, and preview patterns.
- Phase 13 already established first-class tag persistence and many-to-many account-tag associations.
- Phase 14 already established first-class tag CRUD, canonical tag-name storage, and reusable tag administration helpers.
- Current account workflows already use presenter-driven selection tables and defaults; tag selection should follow that same interaction model rather than introducing a separate interaction style.
- Current account listing already surfaces institution in a dedicated Rich table, so tag display should be added to that table rather than introduced as a separate detail command.

Tone and implementation expectations:

- Keep CLI ergonomics explicit and low-friction.
- Prefer readable tables and obvious prompts over compact but ambiguous input.
- Make the untagged state explicit in previews without making it feel like an error.
- Keep the phase narrow and independently shippable so later reporting and compatibility phases can build on it cleanly.
