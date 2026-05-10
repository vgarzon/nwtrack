# Phase 17 Validation: New Single-Month Aggregated Balance Report

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [ ] CLI Contract And Workflow Wiring
- [ ] Interactive Input Flow
- [ ] Report Presentation
- [ ] Validation And Compatibility

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260510-phase-17-new-single-month-aggregated-balance-report/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document defines `reports balances-aggregate` as the new Phase 17 command surface.
- The requirements document defines `--month`, `--dimension`, `--currency`, and `--status-scope` as the supported inputs.
- The requirements document states that the command supports hybrid execution using explicit flags and interactive prompt fallback.
- The requirements document states that `status_scope` defaults to `active`.
- The requirements document states that mixed-currency non-`currency` requests must prompt for currency when interactive and fail clearly with `--currency` guidance when not.
- The requirements document states that the output is one grouped balances table rather than a reuse of the legacy category-summary report layout.
- The requirements document states that empty valid results are successful and show a no-data message.
- The requirements document states that legacy report commands remain unchanged in this phase.

Feature-specific implementation tests required by this phase:

- A CLI smoke test proves `reports --help` exposes `balances-aggregate`.
- A workflow or presenter test proves the report can prompt for month when `--month` is omitted.
- A workflow or presenter test proves the report can prompt for dimension when `--dimension` is omitted.
- A workflow or presenter test proves quitting from month selection exits cleanly.
- A workflow or presenter test proves quitting from dimension selection exits cleanly.
- A workflow or presenter test proves an interactive mixed-currency non-`currency` request prompts for currency selection.
- A workflow or presenter test proves quitting from currency selection exits cleanly.
- A workflow test proves a non-interactive mixed-currency non-`currency` request fails clearly without `--currency`.
- A workflow test proves a single-currency non-`currency` request succeeds without `--currency`.
- A workflow test proves `status_scope=all` reaches the shared aggregation request unchanged.
- A presenter or renderer test proves grouped output uses the selected dimension as the first column label.
- A presenter or renderer test proves `Unassigned` and `Untagged` labels are rendered unchanged when returned by the shared layer.
- A workflow or presenter test proves empty results show a no-data message and do not render an empty table.
- A regression test proves `reports balances-category` remains registered and behaviorally unchanged.
- A regression test proves `reports networth-history` remains registered and behaviorally unchanged.

## Manual

1. Run `nwtrack reports balances-aggregate` with no flags and confirm the workflow prompts for month and dimension, then prints one grouped balances table.
2. Run `nwtrack reports balances-aggregate --month 2025-11 --dimension category` in a single-currency fixture and confirm it completes without a currency prompt.
3. Run `nwtrack reports balances-aggregate --month 2025-11 --dimension institution` in a mixed-currency fixture without `--currency` and confirm the interactive flow prompts for currency selection.
4. Run the same mixed-currency non-`currency` request in a non-interactive context and confirm it fails with guidance to provide `--currency`.
5. Run `nwtrack reports balances-aggregate --month 2025-11 --dimension currency` and confirm grouped rows remain separated by currency.
6. Run `nwtrack reports balances-aggregate --month 2025-11 --dimension tag` and confirm `Untagged` appears when accounts without tags exist.
7. Run `nwtrack reports balances-aggregate --month 2025-11 --dimension institution` and confirm `Unassigned` appears when accounts without institutions exist.
8. Run the command for a month with no balances and confirm it shows a no-data message rather than an empty table or stack trace.
9. Confirm `nwtrack reports balances-category` still runs and displays the existing category summary output.
10. Confirm `nwtrack reports networth-history` still runs and displays the existing net worth history output.

## Tone Check

- The spec uses explicit CLI language rather than describing the feature only in data-layer terms.
- The hybrid flag-plus-prompt workflow is described clearly enough to implement without inventing new interaction patterns.
- Mixed-currency behavior is stated in user-facing CLI terms, including `--currency` guidance.
- The output remains conservative and readable for a first dedicated aggregation report command.
- Deferrals are clear enough that later history and compatibility-convergence phases can build on this phase without re-specifying the command contract.

## Definition Of Done

- The Phase 17 spec directory exists with the three required documents.
- The spec defines the new single-month aggregated report command, its inputs, its mixed-currency behavior, and its presentation contract clearly enough for implementation.
- The spec preserves current product direction by keeping legacy report commands unchanged and deferring history, convergence, and currency-conversion work.
- The spec names the automated tests, manual checks, and quality gates needed to validate the feature.
