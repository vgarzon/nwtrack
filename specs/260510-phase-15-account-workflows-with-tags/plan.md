# Phase 15 Plan: Account Workflows With Tags

## 1. Account Input And Presenter Updates

1. Extend account creation and update workflow inputs to carry zero-to-many tag selection immediately after institution selection.
2. Add indexed multi-select tag collection and tag display support to the account presenters.
3. Use comma-separated indexes, with `0` for no tags and `q` for quit.

## 2. Minimal Tag Fetch And Read Support

1. Extend account-facing fetch support only as needed to retrieve tags for presenter selection.
2. Add only the account-tag reads needed to preload current tags for update and to render account-facing output.
3. Preserve existing account read behavior for accounts that have zero tags assigned.

## 3. Account Use Case Integration

1. Thread `tag_ids` through `accounts create` and persist account-tag links after account creation.
2. Thread `tag_ids` through `accounts update`, including keep, replace, and clear behavior.
3. Ensure create and update previews and success verification show and validate tags consistently.

## 4. Account List And Preview Output

1. Add tag display to the account list table.
2. Place the `Tags` column immediately after `Name`.
3. Render multi-tag values as a comma-separated alphabetical list and render zero tags as blank in tables.
4. Keep active-only behavior and the rest of the account list flow unchanged.

## 5. Validation And Compatibility

1. Add automated tests for create, update, and list behavior with zero, one, and many tags.
2. Add manual checks for indexed multi-select behavior, empty-tag handling, keep/replace/clear update behavior, and tag display formatting.
3. Run and record the required quality gates for linting, type checking, and tests.
