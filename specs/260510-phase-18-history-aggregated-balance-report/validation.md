# Phase 18 Validation: History Aggregated Balance Report

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Shared History Aggregation Contracts
- [X] History Aggregation Use Case
- [X] CLI Contract And Interactive Flow
- [X] History Report Presentation
- [X] Validation And Compatibility

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260510-phase-18-history-aggregated-balance-report/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document defines `reports balances-aggregate-history` as the new Phase 18 command surface.
- The requirements document defines `--start-month`, `--end-month`, `--dimension`, `--currency`, and `--status-scope` as the supported inputs.
- The requirements document states that the selected history range is inclusive of both endpoints.
- The requirements document defines shared request and result DTOs for history aggregation rather than overloading the single-month types.
- The requirements document states that the command supports hybrid execution using explicit flags and interactive prompt fallback.
- The requirements document states that `status_scope` defaults to `active`.
- The requirements document states that mixed-currency non-`currency` history requests must prompt for currency when interactive and fail clearly with `--currency` guidance when not.
- The requirements document states that the output is one long grouped history table rather than a reuse of the legacy net-worth-history layout.
- The requirements document states that empty months are omitted rather than rendered as synthetic zero rows.
- The requirements document states that empty valid results are successful and show a no-data message.
- The requirements document states that legacy report commands remain unchanged in this phase.

Feature-specific implementation tests required by this phase:

- A DTO or use-case test proves a valid inclusive history range is accepted.
- A use-case test proves a reversed range where `start_month > end_month` fails clearly.
- A use-case test proves non-`currency` history aggregation rejects mixed-currency input when no `currency_code` is supplied.
- A use-case test proves a single-currency non-`currency` history request succeeds without `--currency`.
- A use-case test proves `currency` history aggregation may run without `--currency`.
- A query or use-case test proves category history aggregation returns the expected grouped totals across multiple months.
- A query or use-case test proves side history aggregation returns `asset` before `liability` within each month.
- A query or use-case test proves institution history aggregation includes an `Unassigned` bucket when applicable.
- A query or use-case test proves currency history aggregation groups by currency code without cross-currency summation.
- A query or use-case test proves tag history aggregation includes an `Untagged` bucket when applicable.
- A query or use-case test proves a multi-tag account contributes its full amount to every assigned tag group within each month.
- A query or use-case test proves `status_scope=all` includes inactive-account balances.
- A query or use-case test proves months with no matching balances are omitted from the history result.
- A CLI smoke test proves `reports --help` exposes `balances-aggregate-history`.
- A workflow or presenter test proves the report can prompt for start month when `--start-month` is omitted.
- A workflow or presenter test proves the report can prompt for end month when `--end-month` is omitted.
- A workflow or presenter test proves the report can prompt for dimension when `--dimension` is omitted.
- A workflow or presenter test proves quitting from start-month selection exits cleanly.
- A workflow or presenter test proves quitting from end-month selection exits cleanly.
- A workflow or presenter test proves quitting from dimension selection exits cleanly.
- A workflow or presenter test proves an interactive mixed-currency non-`currency` history request prompts for currency selection.
- A workflow or presenter test proves quitting from currency selection exits cleanly.
- A workflow or presenter test proves the long-table output uses `Month` plus the selected dimension as visible columns.
- A workflow or presenter test proves `Unassigned` and `Untagged` labels are rendered unchanged when returned by the shared layer.
- A workflow or presenter test proves empty results show a no-data message and do not render an empty table.
- A regression test proves `reports balances-aggregate` remains registered and behaviorally unchanged.
- A regression test proves `reports balances-category` remains registered and behaviorally unchanged.
- A regression test proves `reports networth-history` remains registered and behaviorally unchanged.

## Manual

1. Run `nwtrack reports balances-aggregate-history` with no flags and confirm the workflow prompts for start month, end month, and dimension, then prints one grouped history table.
2. Run `nwtrack reports balances-aggregate-history --start-month 2025-09 --end-month 2025-11 --dimension category` in a single-currency fixture and confirm it completes without a currency prompt.
3. Run `nwtrack reports balances-aggregate-history --start-month 2025-09 --end-month 2025-11 --dimension institution` in a mixed-currency fixture without `--currency` and confirm the interactive flow prompts for currency selection.
4. Run the same mixed-currency non-`currency` request in a non-interactive context and confirm it fails with guidance to provide `--currency`.
5. Run `nwtrack reports balances-aggregate-history --start-month 2025-09 --end-month 2025-11 --dimension currency` and confirm grouped rows remain separated by currency.
6. Run `nwtrack reports balances-aggregate-history --start-month 2025-09 --end-month 2025-11 --dimension tag` and confirm `Untagged` appears when accounts without tags exist.
7. Run `nwtrack reports balances-aggregate-history --start-month 2025-09 --end-month 2025-11 --dimension institution` and confirm `Unassigned` appears when accounts without institutions exist.
8. Run the command for a range that includes months without balances and confirm those months are omitted rather than shown as zero rows.
9. Run the command for a range with no matching balances at all and confirm it shows a no-data message rather than an empty table or stack trace.
10. Run the command with `--start-month 2025-11 --end-month 2025-09` and confirm it fails clearly before querying.
11. Confirm `nwtrack reports balances-aggregate` still runs and displays the existing single-month grouped output.
12. Confirm `nwtrack reports balances-category` still runs and displays the existing category summary output.
13. Confirm `nwtrack reports networth-history` still runs and displays the existing net worth history output.

## Tone Check

- The spec uses explicit CLI language rather than describing the feature only in data-layer terms.
- The hybrid flag-plus-prompt workflow is described clearly enough to implement without inventing new interaction patterns.
- Mixed-currency behavior is stated in user-facing CLI terms, including `--currency` guidance.
- The output remains conservative and readable for the first dedicated history aggregation command.
- Deferrals are clear enough that Phase 19 compatibility convergence can build on this phase without re-specifying the command contract.

## Definition Of Done

- The Phase 18 spec directory exists with the three required documents.
- The spec defines the new history aggregated report command, its inputs, its mixed-currency behavior, and its presentation contract clearly enough for implementation.
- The spec defines the shared history request and result contracts clearly enough for implementation below the CLI layer.
- The spec preserves current product direction by keeping legacy report commands unchanged and deferring compatibility convergence, currency-conversion, and gap-filling behavior.
- The spec names the automated tests, manual checks, and quality gates needed to validate the feature.
