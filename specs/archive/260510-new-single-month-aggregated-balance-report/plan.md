# Phase 17 Plan: New Single-Month Aggregated Balance Report

## 1. CLI Contract And Workflow Wiring

1. Add `reports balances-aggregate` to the Typer report command surface with `--month`, `--dimension`, `--currency`, and `--status-scope`.
2. Add one application-level workflow that gathers missing inputs, builds a `SingleMonthAggregationRequest`, runs the shared aggregation use case, and maps outcomes to presenter calls.
3. Keep the workflow additive and leave existing report commands untouched.

## 2. Interactive Input Flow

1. Reuse the existing reporting month-selection pattern when `--month` is omitted.
2. Add one explicit dimension-selection prompt when `--dimension` is omitted.
3. Add a mixed-currency currency-selection prompt for interactive non-`currency` requests that would otherwise fail without `--currency`.

## 3. Report Presentation

1. Add a presenter contract and Rich implementation for the single-month aggregated report workflow.
2. Add one grouped balances table renderer that uses the selected dimension as the first column and preserves shared-layer ordering and labels.
3. Add user-facing empty-state, quit, and validation messaging for month, dimension, and mixed-currency cases.

## 4. Validation And Compatibility

1. Add automated tests for the new CLI command registration, workflow input handling, and grouped report output.
2. Add regression checks proving the existing `balances-category` and `networth-history` commands remain unchanged in this phase.
3. Run and record the required quality gates for linting, type checking, and tests.
