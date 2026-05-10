# Phase 15 Validation: Account Workflows With Tags

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Account Input And Presenter Updates
- [ ] Minimal Tag Fetch And Read Support
- [ ] Account Use Case Integration
- [ ] Account List And Preview Output
- [ ] Validation And Compatibility

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260510-phase-15-account-workflows-with-tags/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document defines `accounts create`, `accounts update`, and `accounts list` as the Phase 15 workflow surface.
- The requirements document states that tag selection uses indexed multi-select with comma-separated indexes.
- The requirements document states that tag selection is collected immediately after institution selection in create and update.
- The requirements document states that `0` selects no tags and `q` quits the tag selector.
- The requirements document states that update defaults to the current tag set and allows an explicit clear-all path.
- The requirements document states that create and update continue to work when no tags exist.
- The requirements document states that account list output and create/update previews surface tags in this phase.
- The requirements document states that multi-tag display uses a comma-separated alphabetical list and that zero tags render as blank in tables.
- The requirements document states that fetch-service changes remain minimal and phase-scoped.
- The requirements document states that reporting, CSV, and aggregation-semantics changes remain deferred.

Feature-specific implementation tests required by this phase:

- A use-case or workflow test proves account creation succeeds with zero tags assigned.
- A use-case or workflow test proves account creation succeeds with one selected tag.
- A use-case or workflow test proves account creation succeeds with multiple selected tags.
- A use-case or workflow test proves account update can keep an existing multi-tag selection by accepting the default.
- A use-case or workflow test proves account update can replace one tag set with another.
- A use-case or workflow test proves account update can clear all tags explicitly.
- A workflow or presenter test proves create and update collect tag selection immediately after institution selection.
- A workflow or presenter test proves the tag selector accepts comma-separated indexes and rejects invalid indexes clearly.
- A workflow or presenter test proves repeated selected indexes collapse to one tag assignment.
- A workflow test proves account create still works when no tags exist.
- A workflow test proves account update still works when no tags exist.
- A presenter, CLI, or renderer test proves account list output adds the `Tags` column immediately after `Name`.
- A presenter, CLI, or renderer test proves multi-tag account output is alphabetical and comma-separated.
- A presenter, CLI, or renderer test proves zero-tag accounts render blank table cells and explicit preview output.
- A fetch-service or equivalent read-layer test proves the new tag read support is limited to what account workflows need.
- A regression test proves existing institution-aware account workflow behavior remains unchanged apart from the new tag step and tag display.

## Manual

1. Run `nwtrack accounts create` and confirm tag selection appears immediately after institution selection, accepts zero, one, or many tags, and allows `q` to quit safely.
2. Confirm `accounts create` still works cleanly when there are no tags in the database.
3. Run `nwtrack accounts update` and confirm tag selection defaults to the current assigned tags.
4. Confirm `accounts update` allows keeping the current tags, replacing them with a different selection, or clearing all tags with `0`.
5. Run `nwtrack accounts list` and confirm the table places `Tags` immediately after `Name`.
6. Confirm zero-tag accounts show blank cells in account tables.
7. Confirm single-tag and multi-tag accounts show normalized tag names in alphabetical comma-separated form.
8. Confirm account create/update previews show `None` when no tags are assigned and show the same alphabetical list when tags are assigned.
9. Confirm existing active-only account listing behavior remains unchanged apart from the new tags column.
10. Confirm reporting, balance, export, and tag-administration workflows remain unchanged in this phase.

## Tone Check

- The spec uses CLI-first language and keeps prompt and output behavior explicit.
- The zero-tags path is described as normal supported behavior, not as an exception path.
- Indexed multi-select behavior is stated concretely enough that prompts, validation, and tests can share one rule.
- Deferrals are stated clearly so later reporting phases can own aggregation semantics without ambiguity.

## Definition Of Done

- The Phase 15 spec directory exists with the three required documents.
- The spec defines account create, update, and list tag behavior clearly enough for implementation.
- The spec locks in indexed multi-select tag assignment, explicit clear behavior, and stable tag rendering.
- The spec preserves compatibility for existing zero-tag accounts.
- The spec names the automated tests, manual checks, and quality gates needed to validate the feature.
