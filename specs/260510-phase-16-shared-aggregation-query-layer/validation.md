# Phase 16 Validation: Shared Aggregation Query Layer

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Reporting Contracts And DTOs
- [X] Shared Single-Month Aggregation Use Case
- [ ] SQLAlchemy Aggregation Query Layer
- [ ] Wiring And Compatibility Boundary
- [ ] Validation And Regression Coverage

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260510-phase-16-shared-aggregation-query-layer/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document defines one generic single-month aggregation interface rather than separate public methods per dimension.
- The requirements document defines support for `category`, `side`, `institution`, `currency`, and `tag` aggregation.
- The requirements document states that account-status filtering is supported and defaults to active-only.
- The requirements document states that non-`currency` aggregation fails clearly rather than producing mixed-currency sums when multiple currencies are present and no currency filter is supplied.
- The requirements document states that institution aggregation includes an explicit unassigned bucket.
- The requirements document states that tag aggregation includes an explicit untagged bucket.
- The requirements document states that multi-tag accounts contribute their full balance to every assigned tag group.
- The requirements document states that this phase does not add a new CLI command or migrate existing report commands onto the shared core.

Feature-specific implementation tests required by this phase:

- A DTO or use-case test proves the default status scope is active-only.
- A use-case test proves non-`currency` aggregation rejects mixed-currency input when no `currency_code` is supplied.
- A use-case test proves non-`currency` aggregation succeeds when a valid `currency_code` filter is supplied.
- A query or use-case test proves category aggregation returns the expected grouped totals for one month.
- A query or use-case test proves side aggregation returns `asset` before `liability`.
- A query or use-case test proves institution aggregation includes an `Unassigned` bucket when applicable.
- A query or use-case test proves currency aggregation groups by currency code without cross-currency summation.
- A query or use-case test proves tag aggregation includes an `Untagged` bucket when applicable.
- A query or use-case test proves a multi-tag account contributes its full amount to every assigned tag group.
- A query or use-case test proves `status_scope=ALL` includes inactive-account balances.
- A query or use-case test proves a valid request with no matching balances returns an empty group list rather than an error.
- A regression test proves the existing category report workflow still passes without requiring the new CLI command surface.
- A regression test proves the existing net worth history workflow still passes without being rewritten in this phase.

## Manual

1. Review the spec and confirm Phase 16 is limited to shared single-month aggregation logic below the CLI layer.
2. Confirm the requirements document defines the request and result shapes clearly enough for implementation.
3. Confirm mixed-currency protection is explicit for all non-`currency` aggregation.
4. Confirm category, side, institution, currency, and tag are all listed as supported dimensions.
5. Confirm institution aggregation includes `Unassigned` and tag aggregation includes `Untagged`.
6. Confirm multi-tag semantics are stated explicitly as full-amount duplication across assigned tags.
7. Confirm active-only is the default while all-account aggregation remains available explicitly.
8. Confirm existing report commands are treated as unchanged compatibility surfaces in this phase.
9. Confirm no new CLI command design, history aggregation behavior, or compatibility migration is pulled into this phase.

## Tone Check

- The spec uses precise CLI-first and accounting-correct language.
- Validation behavior is explicit where mixed-currency aggregation would be invalid.
- Deferrals are stated clearly so later reporting phases can own CLI design and compatibility migration.
- The phase stays narrow and independently shippable.

## Definition Of Done

- The Phase 16 spec directory exists with the three required documents.
- The spec defines one shared single-month aggregation core with explicit semantics for every supported dimension.
- The spec names the request/result contracts, validation rules, and grouping rules clearly enough for implementation.
- The spec preserves roadmap boundaries by deferring new CLI command design, history aggregation, and compatibility-command migration.
- The spec names the automated tests, manual checks, and quality gates needed to validate the feature.
