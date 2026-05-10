# Phase 19 Plan: Compatibility Convergence

## 1. Compatibility Reporting Contracts

1. Define the compatibility behavior for `reports balances-category` and `reports networth-history` in terms of the shared aggregation model instead of the legacy bespoke report paths.
2. Add any internal helper contracts needed to discover the latest months with shared aggregation data for one dimension, currency, and status scope.
3. Keep the public CLI command surface unchanged in this phase.

## 2. Legacy Command Convergence

1. Rework `reports balances-category` so category totals come from shared single-month aggregation by `category`.
2. Rework the same workflow so its net-worth section comes from shared single-month aggregation by `side` in USD.
3. Rework `reports networth-history` so it derives its history data from shared history aggregation by `side` in USD while preserving the current `n_months` and `n_years` workflow.
4. Add compatibility mappers that transform shared aggregation results back into the legacy presenter-facing DTOs rather than rewriting the presenter layouts.

## 3. Correctness And Error Handling

1. Make mixed-currency `reports balances-category` requests fail clearly instead of producing invalid grouped totals.
2. Preserve current no-data, partial-data, cancellation, and invalid-input handling where those behaviors are already part of the legacy commands.
3. Record the long-term direction that consolidated reporting should use one explicit reporting currency, with USD as the initial target once conversion support exists.

## 4. Validation And Constitution Updates

1. Add automated tests covering the shared-core convergence paths, compatibility mappings, and mixed-currency failure behavior.
2. Add regression checks proving the legacy command names, arguments, prompts, and layouts remain unchanged where the spec requires compatibility.
3. Update constitution-level guidance where needed so the roadmap and stack guidance record the deferred single-reporting-currency direction.
4. Run and record the required quality gates for linting, type checking, and tests.
