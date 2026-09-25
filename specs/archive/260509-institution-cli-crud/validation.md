# Phase 11 Validation: Institution CLI CRUD

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Institution CLI Surface
- [X] Presenter And UI Support
- [X] Use Cases And Repository Extensions
- [X] Delete Safety And Validation
- [X] Validation

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260509-phase-11-institution-cli-crud/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document defines `institutions list/create/update/delete` as the Phase 11 CLI surface.
- The requirements document states that update and delete select institutions by numeric ID.
- The requirements document states that institution admin views surface linked-account usage counts.
- The requirements document states that deletion is blocked when any account still references the institution.
- The requirements document states that CSV and account workflow changes remain deferred.
- The requirements document states that fetch-service institution methods remain deferred.

Feature-specific implementation tests required by this phase:

- A use-case or CLI test proves `institutions list` displays institutions with usage counts.
- A use-case or CLI test proves `institutions create` succeeds and shows the refreshed list.
- A use-case or CLI test proves create rejects a duplicate institution name case-insensitively.
- A use-case or CLI test proves `institutions update` succeeds for a valid institution selected by ID.
- A use-case or CLI test proves update rejects a duplicate institution name case-insensitively.
- A use-case or CLI test proves `institutions delete` succeeds when the selected institution has zero linked accounts.
- A use-case or CLI test proves delete is blocked when the selected institution is still referenced by one or more accounts.
- A workflow test proves update exits cleanly when no institutions exist.
- A workflow test proves delete exits cleanly when no institutions exist.
- A workflow test proves create, update, and delete cancellation paths remain readable and safe.
- A repository test proves institution update works.
- A repository test proves institution delete-by-id works when allowed.
- A repository test proves linked-account counts are computed correctly for institutions.

## Manual

1. Run `nwtrack institutions list` and confirm the table includes `ID`, `Name`, `Description`, and `Accounts`.
2. Confirm `institutions list` handles the empty state cleanly when no institutions exist.
3. Run `nwtrack institutions create` and confirm the workflow shows a preview, respects cancellation, and displays the refreshed list on success.
4. Confirm create rejects a duplicate institution name with a clear validation message.
5. Run `nwtrack institutions update` and confirm institution selection is by ID, invalid IDs re-prompt, and current values are used as defaults.
6. Confirm update rejects a duplicate institution name with a clear validation message.
7. Run `nwtrack institutions delete` and confirm the workflow previews the selected institution before confirmation.
8. Confirm delete succeeds for an unreferenced institution.
9. Confirm delete is blocked for a referenced institution and that the message includes the linked-account count.
10. Confirm account create, update, list, and detail workflows remain unchanged in this phase.
11. Confirm no CSV import/export behavior changes are introduced in this phase.

## Tone Check

- The spec uses precise CLI-first language rather than abstract CRUD terminology alone.
- Interactive prompts and validation are described clearly enough to preserve CLI ergonomics.
- Delete safety is explicit and conservative.
- Deferrals are stated clearly so Phase 12 can own account workflow integration without ambiguity.

## Definition Of Done

- The Phase 11 spec directory exists with the three required documents.
- The spec defines the institution CLI surface, presenter boundaries, and repository additions clearly enough for implementation.
- The spec locks in delete restriction behavior for referenced institutions.
- The spec preserves Phase 10 boundaries by deferring account workflow, fetch-service, reporting, and CSV changes.
- The spec names the automated tests, manual checks, and quality gates needed to validate the feature.
