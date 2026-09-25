# Phase 17 Requirements: New Single-Month Aggregated Balance Report

## Scope

This phase exposes the shared single-month aggregation core through one new additive CLI report command without changing the existing compatibility report commands.

Included in this phase:

- Add one new `reports balances-aggregate` command for grouped single-month balances
- Accept one month, one aggregation dimension, an optional currency filter, and an optional status scope
- Support hybrid CLI ergonomics where flags may be provided directly and missing required inputs may be collected interactively
- Add presenter-driven Rich output for the new grouped report
- Reuse the shared Phase 16 aggregation request/result layer rather than adding new report-specific query logic
- Keep existing `reports balances-category` and `reports networth-history` commands available and behaviorally unchanged

Not included in this phase:

- History aggregation across a month range
- Migration of older report commands onto the shared aggregation core
- New aggregation dimensions beyond `category`, `side`, `institution`, `currency`, and `tag`
- Currency conversion or exchange-rate-based reporting
- New CSV import/export behavior
- A broader report navigation redesign or TUI-specific report surface

### Report Command Surface

This phase adds one new report command:

- `reports balances-aggregate`

Supported options:

| Option | Type | Default | Notes |
|-------|------|---------|-------|
| `--month` | `YYYY-MM` | Prompt when omitted | One month only |
| `--dimension` | `category \| side \| institution \| currency \| tag` | Prompt when omitted | One grouping dimension only |
| `--currency` | `str` | `None` | Optional explicit currency filter |
| `--status-scope` | `active \| all` | `active` | Advanced opt-in for inactive inclusion |

CLI expectations for this phase:

- The command is additive and does not replace any existing report command.
- The command may run fully from flags, fully interactively, or as a hybrid of both.
- Missing `month` uses the existing recent-month/custom-month selection pattern already established in reporting workflows.
- Missing `dimension` uses one explicit prompt listing the supported aggregation dimensions.
- `status_scope` defaults to `active` and is not routinely prompted for in the interactive flow.
- The command remains presenter-driven rather than embedding direct console logic in the use case.

### Aggregation Inputs And Defaults

This phase reuses the shared request shape from Phase 16 and adds CLI behavior on top of it.

Required behavior:

- The command requests exactly one month and one aggregation dimension.
- `status_scope=active` includes only active accounts.
- `status_scope=all` includes active and inactive accounts.
- `currency` aggregation may run without `--currency`.
- Non-`currency` aggregation may run without `--currency` only when the selected month and status scope resolve to one currency.
- If non-`currency` aggregation would span multiple currencies and `--currency` is missing, the CLI must not produce invalid mixed-currency totals.

### Mixed-Currency Behavior

This phase defines the user-facing behavior for mixed-currency non-`currency` requests.

Required behavior:

- If `--currency` is provided, the command uses it directly.
- If the command is running interactively and the selected month/scope contains multiple currencies for a non-`currency` aggregation, the workflow prompts the user to choose one currency before running the report.
- The interactive currency prompt uses explicit available currency choices derived from the selected month and status scope.
- If the command is being run without prompt fallback and a mixed-currency non-`currency` request lacks `--currency`, the command fails with clear validation-style feedback telling the user to provide `--currency`.
- The CLI wording must refer to the CLI option name `--currency`, not an internal DTO field name.

### Output And Presentation

This phase introduces one dedicated grouped-report presentation flow.

Required output behavior:

- The workflow shows a report header for the new aggregated report command.
- The report output includes one grouped balances table and does not also show the legacy account list, raw balance list, or separate net worth summary.
- The grouped balances table uses the selected aggregation dimension as the first column label.
- The grouped balances table includes an `Amount` column.
- For non-`currency` aggregation, the resolved report currency is shown in the header or title context rather than duplicated in every row.
- For `currency` aggregation, each currency remains distinct in the grouped rows and no single report currency is implied.
- Group ordering follows the deterministic ordering returned by the shared aggregation layer.
- Group labels such as `Unassigned` and `Untagged` are rendered exactly as returned by the shared aggregation result.

### Empty And Error Behavior

This phase makes empty and invalid report outcomes explicit at the CLI layer.

Required behavior:

- A valid request with no matching balances remains a successful workflow outcome.
- Empty results show a clear no-data message and do not render an empty table.
- Invalid month input uses the existing reporting-style validation feedback.
- Unsupported or malformed dimension input is rejected clearly before the shared aggregation request is executed.
- Mixed-currency non-`currency` requests without an explicit or interactively selected currency are rejected clearly instead of producing invalid totals.
- Quitting during interactive month, dimension, or currency selection exits the workflow cleanly without partial output.

## Decisions

### Decisions Locked In For This Phase

- Phase 17 adds one new additive command: `reports balances-aggregate`.
- The new command uses a hybrid input model: explicit flags when supplied, interactive prompts for missing required inputs.
- `status_scope` remains an optional advanced flag and defaults to `active`.
- The new CLI workflow wraps the shared Phase 16 single-month aggregation use case instead of introducing new query logic.
- Mixed-currency non-`currency` requests are resolved through an interactive currency choice when prompting is available, or a clear `--currency` validation error when it is not.
- The new report output is conservative: one header and one grouped balances table.
- Existing `reports balances-category` and `reports networth-history` commands remain unchanged in this phase.
- Empty valid results are user-visible but not treated as errors.

### Decisions Explicitly Deferred

- History aggregation and history-report command design
- Converging `balances-category` or `networth-history` onto the shared aggregation core
- Additional report filters beyond month, dimension, currency, and status scope
- Automatic currency conversion or exchange-rate-driven reporting
- Breaking changes to existing report command names or output contracts
- TUI-specific reporting behavior

## Context

This spec should be interpreted through `specs/mission.md`, `specs/roadmap.md`, `specs/tech-stack.md`, `specs/stakeholder-input.md`, and the earlier aggregation phases.

Implementation context for this phase:

- Phase 16 already introduced the shared `SingleMonthAggregationRequest`, `SingleMonthAggregationResult`, and the reporting-query/use-case core beneath the CLI.
- The current CLI already has legacy report commands for category summary and net worth history, and those remain compatibility surfaces during this phase.
- Existing reporting workflows already use presenter-driven month selection and Rich table output; the new command should follow those patterns rather than introducing a separate interaction style.
- The product remains CLI-first, local-first, and monthly-snapshot-based, so report ergonomics should favor explicit prompts and readable output over compact but ambiguous flags alone.

Tone and implementation expectations:

- Use precise CLI-first terminology centered on month, dimension, currency, and grouped balances.
- Prefer explicit validation and obvious prompt flows over implicit fallback behavior.
- Keep the report output readable and conservative for the first dedicated aggregation command.
- Keep the phase independently shippable so later history and compatibility-convergence phases can build on it without reworking the command contract.
