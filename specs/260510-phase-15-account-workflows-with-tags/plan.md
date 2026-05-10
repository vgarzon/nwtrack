# Phase 15 Plan: Account Workflows With Tags

## 1. Account Workflow Contracts And Selection Support

1. Extend account workflow DTOs and presentation contracts to carry zero-to-many selected tag IDs and tag-aware preview/list behavior.
2. Add shared tag-selection prompt and rendering helpers that support indexed multi-select, explicit no-tags selection, validation, and deterministic ordering.
3. Extend fetch/read support only as needed to list selectable tags and expose assigned tags on account reads used by account workflows.

## 2. Account Create Workflow With Tags

1. Add tag selection to `accounts create` immediately after institution selection.
2. Persist selected tag associations as part of the create workflow after account insertion.
3. Update create preview and success-path validation so tagged and untagged accounts are both shown correctly.

## 3. Account Update Workflow With Tags

1. Add tag replacement to `accounts update` immediately after institution selection.
2. Use the account's current tag set as the default selection and allow explicit clearing through the no-tags path.
3. Persist replacement tag associations as part of the update workflow and verify the stored tag set after update.

## 4. Account List And Presentation Updates

1. Add tag display to the account list table with comma-separated tag names and blank cells for untagged accounts.
2. Add tag display to account create and update previews with an explicit `None` label for the untagged case.
3. Keep institution display, account selection, and the rest of the account workflow shape unchanged.

## 5. Validation And Compatibility

1. Add automated tests for tag-aware account presenters, use cases, fetch support, and workflow edge cases.
2. Add regression checks proving tag CRUD, reporting workflows, balance workflows, and CSV/export behavior remain unchanged in this phase.
3. Run and record the required quality gates for linting, type checking, and tests.
