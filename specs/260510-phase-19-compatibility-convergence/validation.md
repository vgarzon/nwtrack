# Phase 19 Validation: Compatibility Convergence

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Compatibility Reporting Contracts
- [X] Legacy Command Convergence
- [ ] Correctness And Error Handling
- [ ] Validation And Constitution Updates

## Implementation Notes

- Compatibility Reporting Contracts: completed. Added a shared reporting-query helper for distinct available aggregation months, exposed it through `FetchService`, and added compatibility mappers for adapting shared category and side aggregation results back into legacy DTO shapes.
- Compatibility Reporting Contracts validation: `uv run pytest tests/sqlite/test_reporting_queries.py tests/services/test_fetch_service.py tests/use_cases/test_report_compatibility.py`
- Legacy Command Convergence: completed. Reworked `reports balances-category` to source category and net-worth sections from shared single-month aggregation, reworked `reports networth-history` to source rows from shared history aggregation, and preserved the existing command surfaces and presenter layouts.
- Legacy Command Convergence validation: `uv run pytest tests/use_cases/test_report_balances_by_category.py tests/use_cases/test_report_networth_history.py tests/entrypoints/test_cli_reports.py`

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260510-phase-19-compatibility-convergence/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document states that Phase 19 converges `reports balances-category` and `reports networth-history` onto the shared aggregation model.
- The requirements document states that the legacy command names and arguments remain unchanged in this phase.
- The requirements document states that `reports balances-category` continues to use the current interactive shape and multi-section output.
- The requirements document states that `reports networth-history` continues to use the current `n_months` and `n_years` behavior plus the existing history and total-change presentation.
- The requirements document states that category totals come from shared aggregation by `category`.
- The requirements document states that net worth compatibility comes from shared aggregation by `side`.
- The requirements document states that shared aggregation results are adapted back into legacy presenter-facing shapes rather than forcing a presenter redesign in this phase.
- The requirements document states that mixed-currency `reports balances-category` requests fail clearly instead of producing invalid totals.
- The requirements document states that USD remains the compatibility reporting currency for legacy net-worth workflows in this phase.
- The requirements document states that currency conversion remains deferred.
- The roadmap or other constitution guidance records the long-term direction toward one explicit reporting currency, with USD as the initial target once conversion-based reporting exists.

Feature-specific implementation tests required by this phase:

- A use-case or workflow test proves `reports balances-category` still renders the expected sections for a single-currency month.
- A use-case or workflow test proves the category-summary values shown by `reports balances-category` are derived from the shared aggregation-by-category path.
- A use-case or workflow test proves the net-worth section shown by `reports balances-category` is derived from the shared aggregation-by-side path in USD.
- A use-case or workflow test proves a mixed-currency `reports balances-category` month fails clearly and does not print invalid grouped totals.
- A use-case or workflow test proves `reports balances-category` still preserves cancellation and invalid-month behavior.
- A use-case or workflow test proves `reports networth-history` still honors the default `n_months` behavior.
- A use-case or workflow test proves `reports networth-history` still honors `n_years` overriding `n_months`.
- A use-case or workflow test proves `reports networth-history` still preserves partial-data warnings when fewer months than requested are available.
- A use-case or workflow test proves `reports networth-history` still renders chronological rows plus the total-change summary.
- A query or service test proves the compatibility month-discovery helper returns deterministic months filtered by dimension, currency, and status scope.
- A mapper test proves shared side-aggregation results convert into legacy `NetWorth` values with the correct asset, liability, and net-worth totals.
- A regression test proves `reports --help` still exposes `balances-category` and `networth-history`.

## Manual

1. Run `nwtrack reports balances-category` against a single-currency fixture and confirm the workflow still shows the active-accounts table, month selection, balances table, category summary, and USD net-worth table.
2. Run `nwtrack reports balances-category` against a mixed-currency fixture and confirm it fails clearly before printing invalid grouped totals.
3. Confirm the mixed-currency failure message explains that conversion-based consolidated reporting is not available yet.
4. Run `nwtrack reports networth-history` with default arguments and confirm it shows the existing history table and total-change summary.
5. Run `nwtrack reports networth-history` through the existing CLI surface with a year-count input and confirm the year-based override behavior still works.
6. Run `nwtrack reports networth-history` in a fixture with fewer available USD months than requested and confirm the partial-data warning still appears.
7. Confirm `nwtrack reports balances-aggregate` and `nwtrack reports balances-aggregate-history` remain available and unchanged.

## Tone Check

- The spec describes Phase 19 as a compatibility-convergence phase rather than a general report redesign.
- Mixed-currency failure behavior is framed as accounting-correct validation rather than as a temporary implementation accident.
- The spec preserves CLI-first language and existing workflow terminology.
- The deferred single-reporting-currency direction is recorded clearly without implying that conversion exists already.

## Definition Of Done

- The Phase 19 spec directory exists with the three required documents.
- The spec defines how both legacy commands map onto the shared aggregation model clearly enough for implementation.
- The spec preserves the current command contracts while making the mixed-currency correctness rule explicit.
- Constitution guidance is updated where needed to record the deferred single-reporting-currency direction.
- The spec names the automated tests, manual checks, and quality gates needed to validate the phase.
