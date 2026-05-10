# Phase 14 Validation: Tag CLI CRUD

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Tag Command Surface
- [ ] Tag List And Shared Admin Helper
- [ ] Tag Create And Update Workflows
- [ ] Tag Delete Workflow
- [ ] Validation And Compatibility

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260509-phase-14-tag-cli-crud/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document defines `tags list/create/update/delete` as the Phase 14 CLI surface.
- The requirements document states that update and delete select tags by numeric ID.
- The requirements document states that tag admin views surface linked-account usage counts.
- The requirements document states that deletion is blocked when any account still references the tag.
- The requirements document states that tag names are normalized by trimming whitespace, collapsing repeated whitespace, and lowercasing before storage.
- The requirements document states that account workflow, reporting, fetch-service, and CSV changes remain deferred.

Feature-specific implementation tests required by this phase:

- A CLI smoke test proves the `tags` command group is registered.
- A CLI smoke test proves `tags list`, `tags create`, `tags update`, and `tags delete` are registered.
- A presenter test proves the tag list presenter handles both empty and populated states.
- A presenter test proves create success output shows the refreshed list.
- A presenter test proves duplicate-name validation is shown clearly for create and update.
- A presenter test proves delete blocked messaging includes the linked-account count.
- A presenter test proves create, update, and delete cancellation paths remain readable and safe.
- A use-case test proves `tags list` displays tags with linked-account counts.
- A use-case test proves `tags create` succeeds and shows the refreshed list.
- A use-case test proves create rejects a duplicate tag name after normalization.
- A use-case test proves create rejects a name that becomes empty after normalization.
- A use-case test proves `tags update` succeeds for a valid tag selected by ID.
- A use-case test proves update rejects a duplicate tag name after normalization.
- A use-case test proves `tags delete` succeeds when the selected tag has zero linked accounts.
- A use-case test proves delete is blocked when the selected tag is still referenced by one or more accounts.
- A workflow test proves update exits cleanly when no tags exist.
- A workflow test proves delete exits cleanly when no tags exist.
- A unit or workflow test proves normalization trims leading and trailing whitespace before storage.
- A unit or workflow test proves repeated internal whitespace collapses to single spaces before storage.
- A unit or workflow test proves stored tag names are lowercased.
- A regression test proves current account workflows do not require or expose new tag input in this phase.
- A regression test proves CSV import/export behavior remains unchanged in this phase.

## Manual

1. Run `nwtrack tags list` and confirm the table includes `ID`, `Name`, `Description`, and `Accounts`.
2. Confirm `tags list` handles the empty state cleanly when no tags exist.
3. Run `nwtrack tags create` and confirm the workflow shows a preview, respects cancellation, and displays the refreshed list on success.
4. Confirm create stores the normalized lowercase name after trimming and collapsing repeated whitespace.
5. Confirm create rejects a duplicate tag name when the conflict differs only by whitespace or casing.
6. Run `nwtrack tags update` and confirm tag selection is by ID, invalid IDs re-prompt, and current values are used as defaults.
7. Confirm update persists the normalized lowercase name and rejects normalized duplicates clearly.
8. Run `nwtrack tags delete` and confirm the workflow previews the selected tag before confirmation.
9. Confirm delete succeeds for an unreferenced tag.
10. Confirm delete is blocked for a referenced tag and that the message includes the linked-account count.
11. Confirm account create, update, list, and detail workflows remain unchanged in this phase.
12. Confirm no CSV import/export behavior changes are introduced in this phase.

## Tone Check

- The spec uses precise CLI-first language rather than abstract CRUD terminology alone.
- Interactive prompts and validation are described clearly enough to preserve CLI ergonomics.
- Delete safety is explicit and conservative.
- Normalization behavior is stated concretely enough that implementation and tests can share one rule.
- Deferrals are stated clearly so Phase 15 can own account workflow integration without ambiguity.

## Definition Of Done

- The Phase 14 spec directory exists with the three required documents.
- The spec defines the tag CLI surface, presenter boundaries, normalization behavior, and delete restrictions clearly enough for implementation.
- The spec preserves Phase 13 boundaries by deferring account workflow, fetch-service, reporting, and CSV changes.
- The spec names the automated tests, manual checks, and quality gates needed to validate the feature.
