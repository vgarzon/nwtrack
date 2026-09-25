# Phase 19 Requirements: Compatibility Convergence

## Scope

This phase moves the legacy category-summary and net-worth-history report commands onto the shared aggregation model while preserving their existing CLI contracts where practical.

Included in this phase:

- Move `reports balances-category` onto the shared single-month aggregation core
- Move `reports networth-history` onto the shared history aggregation core
- Preserve existing command names, arguments, prompts, and overall report layouts where practical
- Add any internal compatibility-mapping logic needed to adapt shared aggregation results back into the legacy presenter-facing shapes
- Add internal reporting-query support needed to preserve the `networth-history` last-`n`-months workflow without relying on the legacy net worth repository
- Make mixed-currency compatibility-report behavior explicit so the command fails clearly instead of producing invalid totals

Not included in this phase:

- New legacy-command flags or argument redesign
- Replacement or removal of the legacy command names
- Currency conversion or exchange-rate-based reporting
- Replacing the dedicated `balances-aggregate` or `balances-aggregate-history` commands
- Wide-layout history output or CSV-export work from Phase 21
- General reporting redesign beyond the two compatibility commands in scope

### Compatibility Commands In Scope

This phase converges exactly these legacy commands:

- `reports balances-category`
- `reports networth-history`

Compatibility expectations for this phase:

- The commands remain available under the same names.
- Existing arguments remain the same.
- Existing interactive month-selection behavior remains the same where applicable.
- Existing presenter-driven Rich layouts remain the same unless a behavior change is required for correctness.
- Any user-visible change must be explicitly justified by accounting correctness or by the need to express a previously implicit validation rule.

### `reports balances-category`

This command remains a compatibility workflow with its current multi-step shape.

Required behavior:

- The workflow still shows the report header first.
- The workflow still shows the active-accounts table before month selection.
- The workflow still uses the existing recent-month/custom-month selection pattern.
- The workflow still shows the selected-month balances table.
- Category totals are computed from the shared single-month aggregation core using aggregation by `category`.
- Net worth is computed from the shared single-month aggregation core using aggregation by `side`.
- The shared aggregation results are adapted back into the legacy presenter-facing shapes so the existing category-summary and net-worth tables remain usable.
- The command continues to operate on active accounts only.
- The net-worth section remains USD-based in this phase, preserving the legacy compatibility assumption.

### `reports networth-history`

This command remains a compatibility workflow with its current history summary layout.

Required behavior:

- The command still accepts the current `n_months` and `n_years` inputs.
- `n_years`, when provided, still overrides `n_months`.
- The workflow still uses USD as its implicit reporting currency in this phase.
- The workflow still shows the existing header, chronological history table, partial-data warning behavior, and total-change summary.
- Net worth history is computed from the shared history aggregation core using aggregation by `side`.
- Shared history rows are adapted back into the legacy `NetWorth`-style presenter input shape before presentation.
- The command still returns the latest available USD months with data rather than requiring a user-specified month range.

### Shared Aggregation Mapping Requirements

This phase reuses the shared aggregation DTOs and use cases introduced in earlier phases.

Required internal mapping behavior:

- Category summary compatibility uses `SingleMonthAggregationRequest` with `dimension=category`, `status_scope=active`, and the required currency behavior described below.
- Single-month net worth compatibility uses `SingleMonthAggregationRequest` with `dimension=side`, `status_scope=active`, and `currency_code="USD"`.
- Net-worth-history compatibility uses `HistoryAggregationRequest` with `dimension=side`, `status_scope=active`, and `currency_code="USD"`.
- Shared category groups are adapted into the existing `MonthlyCategoryBalance` shape expected by the legacy presenter.
- Shared side groups and history rows are adapted into legacy `NetWorth` records before presentation.
- Side-to-net-worth mapping preserves the existing meaning of assets, liabilities, and net worth as `assets - liabilities`.

### Mixed-Currency Behavior

This phase makes the compatibility behavior for mixed-currency category reporting explicit.

Required behavior:

- `reports balances-category` must not display invalid mixed-currency category totals.
- If the selected month contains more than one currency across active balances and no conversion layer exists, the workflow fails clearly before rendering category totals or net worth totals.
- The error message explains that mixed-currency compatibility reporting is not supported yet and that explicit conversion-based reporting is deferred.
- The workflow may still show pre-aggregation context already collected earlier in the command, such as the accounts table, selected month, and raw balances table, but it must not show invalid grouped totals.
- `reports networth-history` remains USD-only in this phase and therefore does not introduce a new mixed-currency choice or flag surface.

### Internal Query Support

This phase may add one internal reporting-query helper to preserve legacy history semantics while converging on the shared aggregation model.

Required behavior:

- The reporting layer may expose one helper that returns distinct months with aggregation data for one dimension, currency, and status scope.
- The helper is internal infrastructure support for compatibility workflows, not a new end-user reporting surface.
- The helper must return deterministic month ordering suitable for selecting the latest `n` months for `networth-history`.
- The helper must respect the same account-status and currency filters used by the shared aggregation model.

### Empty And Error Behavior

Required behavior:

- A valid compatibility request with no matching data remains a handled workflow outcome, not a stack trace.
- `reports networth-history` preserves its current no-data and partial-data warning behavior.
- `reports balances-category` preserves its existing cancellation and invalid-month behavior.
- Mixed-currency `balances-category` requests fail clearly instead of silently producing invalid totals.
- This phase does not add interactive currency selection, fallback conversion, or silent currency filtering to the legacy commands.

## Decisions

### Decisions Locked In For This Phase

- Phase 19 is an internal convergence phase for the two legacy report commands.
- `reports balances-category` keeps its existing interactive shape and multi-section output.
- `reports networth-history` keeps its current arguments, warning behavior, history layout, and total-change summary.
- No new flags are added to the legacy commands in this phase.
- Shared aggregation results are adapted back into legacy presenter-facing DTO shapes rather than redesigning the presenters first.
- Mixed-currency `balances-category` requests fail clearly for correctness rather than preserving legacy invalid totals.
- `networth-history` continues to behave as a USD compatibility surface in this phase.

### Decisions Explicitly Deferred

- Currency conversion and single-reporting-currency implementation
- Adding explicit `--currency` or month-range flags to the legacy commands
- Replacing legacy layouts with the newer grouped-report layouts
- Removing legacy command names in favor of aliases only
- Phase 21 output-format options such as wide history layout or CSV output
- Any broader reporting navigation or TUI redesign

## Context

This spec should be interpreted through `specs/mission.md`, `specs/roadmap.md`, `specs/tech-stack.md`, and the earlier aggregation phases.

Implementation context for this phase:

- Phase 16 introduced the shared single-month aggregation core below the CLI layer.
- Phase 17 introduced the new grouped single-month report command without changing the legacy commands.
- Phase 18 introduced the shared history aggregation core and the new grouped history report command without changing the legacy commands.
- The current legacy `balances-category` workflow still uses a category-specific query path and a separate USD net-worth fetch path.
- The current legacy `networth-history` workflow still uses a dedicated net-worth repository path and last-`n`-months selection semantics.
- The product remains CLI-first, local-first, and monthly-snapshot-based, with accounting correctness taking precedence over convenience when the two conflict.

Long-term product context:

- The long-term reporting direction is to support one explicit reporting currency for consolidated reporting, with USD as the initial target.
- Until conversion-based reporting exists, compatibility workflows must not sum mixed currencies into one total.

Tone and implementation expectations:

- Preserve existing user workflows where practical, but do not preserve invalid accounting behavior.
- Prefer thin compatibility adapters over parallel reimplementation of aggregation logic.
- Keep the phase independently shippable and narrow enough that later reporting-UX work can build on it without reopening command-convergence decisions.
