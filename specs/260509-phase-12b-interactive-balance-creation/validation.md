# Phase 12b Validation: Interactive Balance Creation

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Command And Presenter Surface
- [X] Create Workflow Integration
- [X] Duplicate And Cancellation Handling
- [ ] Validation

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260509-phase-12b-interactive-balance-creation/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document defines `balances create` as the Phase 12b workflow surface.
- The requirements document states that the workflow shows active accounts and selects the account by account ID.
- The requirements document states that the workflow accepts any valid `YYYY-MM` month.
- The requirements document states that duplicates are rejected and direct the user to `balances update`.
- The requirements document states that other balance commands remain unchanged in this phase.

Feature-specific implementation tests required by this phase:

- A command or use-case test proves `balances create` is registered and runnable.
- A use-case or workflow test proves a missing balance row can be created successfully.
- A use-case or workflow test proves duplicate `(account_id, month)` creation is rejected without overwriting the existing row.
- A workflow test proves duplicate rejection explicitly directs the user to `balances update`.
- A workflow test proves cancellation before confirmation exits without insert.
- A workflow test proves the command exits cleanly when there are no eligible active accounts.
- A presenter or workflow test proves the active-accounts table is shown before account selection.
- A presenter or workflow test proves success output includes a success message and created-balance preview.
- Regression tests prove `balances update`, `balances delete`, `balances roll`, and `balances transfer` remain unchanged by this phase.

## Manual

1. Run `nwtrack balances create` and confirm the active accounts table is shown before account selection.
2. Create a missing balance entry for an active account and confirm the row is inserted only after confirmation.
3. Confirm the success flow shows both a success message and created-balance preview.
4. Attempt to create a duplicate balance for the same account and month and confirm the workflow rejects it clearly.
5. Confirm duplicate messaging explicitly directs the user to `balances update`.
6. Cancel the workflow before confirmation and confirm no balance row is created.
7. Confirm the command exits cleanly when there are no eligible active accounts.
8. Confirm `balances update`, `balances delete`, `balances roll`, and `balances transfer` still behave as before.

## Tone Check

- The spec uses CLI-first language and keeps the workflow explicit.
- Duplicate rejection is described as normal validation behavior rather than an exceptional failure mode.
- The phase remains narrow and additive rather than turning into a broader balance workflow redesign.

## Definition Of Done

- The Phase 12b spec directory exists with the three required documents.
- The spec defines the create workflow, duplicate behavior, and success flow clearly enough for implementation.
- The spec preserves the narrow Phase 12b boundary around a one-row create command.
- The spec names the automated tests, manual checks, and quality gates needed to validate the feature.
