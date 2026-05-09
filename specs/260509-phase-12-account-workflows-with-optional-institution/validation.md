# Phase 12 Validation: Account Workflows With Optional Institution

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Account Input And Presenter Updates
- [X] Minimal Fetch And Read Support
- [X] Account Use Case Integration
- [X] Account List Output
- [ ] Validation

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260509-phase-12-account-workflows-with-optional-institution/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document defines `accounts create`, `accounts update`, and `accounts list` as the Phase 12 workflow surface.
- The requirements document states that institution selection uses indexed choice with an explicit no-institution option.
- The requirements document states that create and update continue to work when no institutions exist.
- The requirements document states that account list output surfaces institution in this phase.
- The requirements document states that fetch-service changes remain minimal and phase-scoped.
- The requirements document states that reporting, CSV, and institution-required behavior remain deferred.

Feature-specific implementation tests required by this phase:

- A use-case or workflow test proves account creation succeeds with no institution assigned.
- A use-case or workflow test proves account creation succeeds with a selected institution.
- A use-case or workflow test proves account update can add an institution to an unassigned account.
- A use-case or workflow test proves account update can change an assigned institution.
- A use-case or workflow test proves account update can clear an assigned institution.
- A workflow or presenter test proves create and update institution selection uses an indexed choice with an explicit no-institution option.
- A workflow test proves account create still works when no institutions exist.
- A workflow test proves account update still works when no institutions exist.
- A presenter, CLI, or renderer test proves account list output includes institution for assigned and unassigned accounts.
- A fetch-service or equivalent read-layer test proves the new institution read support is limited to what account workflows need.

## Manual

1. Run `nwtrack accounts create` and confirm the workflow allows selecting an institution or explicitly choosing no institution.
2. Confirm `accounts create` still works cleanly when there are no institutions in the database.
3. Run `nwtrack accounts update` and confirm the workflow allows keeping, changing, or clearing institution assignment.
4. Confirm `accounts update` still works cleanly when there are no institutions in the database.
5. Run `nwtrack accounts list` and confirm the table includes institution information for mixed assigned and unassigned accounts.
6. Confirm account create/update previews show institution consistently before confirmation.
7. Confirm existing active-only account listing behavior remains unchanged apart from the new institution column.
8. Confirm balance, report, and export workflows remain unchanged in this phase.

## Tone Check

- The spec uses CLI-first language and keeps prompts/output behavior explicit.
- The optional institution path is described as normal supported behavior, not as an exception path.
- The indexed-selection pattern aligns with the existing account workflow conventions.
- Deferrals are stated clearly so later phases can own mandatory-institution rules and broader reporting changes.

## Definition Of Done

- The Phase 12 spec directory exists with the three required documents.
- The spec defines account create, update, and list institution behavior clearly enough for implementation.
- The spec locks in indexed institution selection with an explicit no-institution path.
- The spec preserves compatibility for existing unassigned accounts.
- The spec names the automated tests, manual checks, and quality gates needed to validate the feature.
