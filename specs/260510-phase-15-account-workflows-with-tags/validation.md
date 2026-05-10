# Phase 15 Validation: Account Workflows With Tags

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Account Workflow Contracts And Selection Support
- [X] Account Create Workflow With Tags
- [ ] Account Update Workflow With Tags
- [ ] Account List And Presentation Updates
- [ ] Validation And Compatibility

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260510-phase-15-account-workflows-with-tags/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document defines `accounts create`, `accounts update`, and `accounts list` as the Phase 15 command surface.
- The requirements document states that tag selection uses displayed indices rather than raw tag IDs.
- The requirements document states that tag selection accepts comma-separated multi-select input and has an explicit `0` no-tags path.
- The requirements document states that update edits tags as a full replacement step.
- The requirements document states that account list output gains a `Tags` column with comma-separated names and blank cells for untagged accounts.
- The requirements document states that create and update previews gain a `Tags` field and use `None` for the untagged case.
- The requirements document states that fetch/read support expands only as needed for tag-aware account workflows.
- The requirements document states that reporting, CSV/export, tag CRUD, and balance workflows remain deferred or unchanged in this phase.

Feature-specific implementation tests required by this phase:

- A presenter test proves account create continues cleanly when no tags exist.
- A presenter test proves account create can collect a single selected tag.
- A presenter test proves account create can collect multiple selected tags.
- A presenter test proves invalid multi-select input is rejected clearly and re-prompts.
- A presenter test proves repeated tag indices are deduplicated before preview and persistence.
- A presenter test proves account update uses the current tag set as the default selection.
- A presenter test proves account list renders empty, single-tag, and multi-tag accounts correctly.
- A presenter test proves create and update previews show `Tags` and render `None` for untagged accounts.
- A use-case test proves account create persists zero tags successfully.
- A use-case test proves account create persists one selected tag successfully.
- A use-case test proves account create persists multiple selected tags successfully.
- A use-case test proves account update can replace one tag set with another.
- A use-case test proves account update can clear all tags through the explicit no-tags path.
- A use-case test proves account update verification includes the stored tag set.
- A use-case test proves the workflows continue safely when no tags exist in the system.
- A workflow test proves quitting from the tag-selection step cancels the workflow cleanly.
- A fetch or repository-backed test proves account reads returned to account workflows include assigned tags.
- A fetch or repository-backed test proves tag selection order is deterministic.
- A regression test proves tag CRUD commands remain unchanged in this phase.
- A regression test proves reporting commands remain unchanged in this phase.
- A regression test proves balance create, update, delete, roll-forward, and transfer workflows remain unchanged in this phase.
- A regression test proves CSV import/export behavior remains unchanged in this phase.

## Manual

1. Run `nwtrack accounts create` when no tags exist and confirm the workflow continues without failure and creates an untagged account.
2. Run `nwtrack accounts create` with one selected tag and confirm the preview and stored account show that tag.
3. Run `nwtrack accounts create` with multiple selected tags and confirm the preview and stored account show all selected tags in deterministic order.
4. Confirm invalid tag multi-select input is rejected clearly and that the workflow re-prompts instead of silently accepting bad input.
5. Run `nwtrack accounts update` for an untagged account and confirm tags can be assigned.
6. Run `nwtrack accounts update` for a tagged account and confirm the current tag set is offered as the default selection.
7. Confirm `accounts update` can replace the existing tag set with a different set.
8. Confirm `accounts update` can clear all tags by choosing the explicit no-tags path.
9. Run `nwtrack accounts list` and confirm the table includes `Institution` and `Tags`, with blank tag cells for untagged accounts.
10. Confirm account create and update previews include a `Tags` field and show `None` for untagged accounts.
11. Confirm `nwtrack tags list/create/update/delete` behavior remains unchanged.
12. Confirm report commands and balance workflows remain unchanged.
13. Confirm no CSV import/export behavior changes are introduced in this phase.

## Tone Check

- The spec uses precise CLI-first language rather than abstract data-model terminology alone.
- Interactive tag selection is described clearly enough that create and update can share one predictable interaction pattern.
- The distinction between explicit untagged preview output and blank account-table cells is stated clearly.
- Deferrals are stated clearly so later reporting and compatibility phases can build on this phase without ambiguity.
- The scope remains narrow enough to stay independently shippable.

## Definition Of Done

- The Phase 15 spec directory exists with the three required documents.
- The spec defines tag-aware account create, update, list, preview, and minimal read-support behavior clearly enough for implementation.
- The spec preserves current product direction by deferring reporting, CSV/export, broader account redesign, and tag CRUD changes.
- The spec names the automated tests, manual checks, and quality gates needed to validate the feature.
