# Phase 18 Plan: History Aggregated Balance Report

## 1. Shared History Aggregation Contracts

1. Add shared DTOs for history aggregation request, row, and result shapes.
2. Extend the reporting port and the SQLAlchemy reporting repository with one generic history-range aggregation method.
3. Reuse the existing aggregation dimension and status-scope model rather than introducing history-specific enums or bespoke query paths.

## 2. History Aggregation Use Case

1. Add one application use case that validates inclusive month ranges and executes the shared history aggregation request.
2. Mirror Phase 17 mixed-currency protection for non-`currency` dimensions across the full requested range.
3. Keep the history use case below the CLI layer so later compatibility-report migration can reuse it directly.

## 3. CLI Contract And Interactive Flow

1. Add `reports balances-aggregate-history` to the Typer report command surface with `--start-month`, `--end-month`, `--dimension`, `--currency`, and `--status-scope`.
2. Add one application-level workflow that gathers missing inputs, builds a `HistoryAggregationRequest`, runs the shared history aggregation use case, and maps outcomes to presenter calls.
3. Reuse the existing reporting month-selection pattern for start and end month selection when flags are omitted.
4. Add one explicit dimension-selection prompt when `--dimension` is omitted.
5. Add a mixed-currency currency-selection prompt for interactive non-`currency` history requests that would otherwise fail without `--currency`.

## 4. History Report Presentation

1. Add a presenter contract and Rich implementation for the history aggregated report workflow.
2. Add one long history table renderer that uses `Month`, the selected dimension, and `Amount` as columns and preserves shared-layer ordering and labels.
3. Add user-facing empty-state, quit, range-validation, and mixed-currency messaging for start month, end month, dimension, and currency cases.

## 5. Validation And Compatibility

1. Add automated tests for the new shared history aggregation contracts, query behavior, CLI workflow input handling, and long-table output.
2. Add regression checks proving the existing `reports balances-aggregate`, `reports balances-category`, and `reports networth-history` commands remain unchanged in this phase.
3. Run and record the required quality gates for linting, type checking, and tests.
