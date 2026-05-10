# Phase 16 Plan: Shared Aggregation Query Layer

## 1. Reporting Contracts And DTOs

1. Add shared reporting types for aggregation dimension, account-status scope, single-month request, result, and result groups.
2. Define one shared reporting-query interface and one application-facing use case interface shape around the same request contract.
3. Remove category-only assumptions from reporting contracts where they would block generic aggregation support.

## 2. Shared Single-Month Aggregation Use Case

1. Implement one use case that validates the request, enforces mixed-currency protection, and delegates grouped reads to the reporting-query layer.
2. Return deterministic ordered results for every supported dimension.
3. Keep empty-result handling explicit and separate from invalid-request handling.

## 3. SQLAlchemy Aggregation Query Layer

1. Implement shared SQLAlchemy query support for aggregation by category, side, institution, currency, and tag.
2. Support status scoping and optional currency filtering through one common request shape.
3. Implement explicit unassigned and untagged grouping semantics and full-amount duplication for multi-tag accounts.

## 4. Wiring And Compatibility Boundary

1. Wire the shared reporting-query implementation into the unit-of-work and dependency graph behind a stable reporting interface.
2. Keep existing report command behavior unchanged in this phase.
3. Avoid introducing new CLI commands, presenters, or compatibility rewrites before Phase 17.

## 5. Validation And Regression Coverage

1. Add automated tests for request validation, mixed-currency protection, deterministic ordering, and each supported aggregation dimension.
2. Add regression coverage proving existing report workflows remain unchanged while the new core is added underneath them.
3. Run and record the required quality gates for linting, type checking, and tests.
