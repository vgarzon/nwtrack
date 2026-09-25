# Phase 18 Requirements: History Aggregated Balance Report

## Scope

This phase extends the shared aggregation model from one month to an inclusive month range and exposes that capability through one new additive CLI report command without changing the existing compatibility report commands.

Included in this phase:

- Add shared application-level request and result DTOs for history aggregation across a start and end month
- Add one shared use case that executes a history aggregation request
- Extend the shared reporting-query interface and SQLAlchemy implementation to support history aggregation by `category`, `side`, `institution`, `currency`, and `tag`
- Add one new `reports balances-aggregate-history` command for grouped balance history across an inclusive month range
- Accept a start month, an end month, one aggregation dimension, an optional currency filter, and an optional status scope
- Support hybrid CLI ergonomics where flags may be provided directly and missing required inputs may be collected interactively
- Add presenter-driven Rich output for the new history report using one long table
- Reuse shared aggregation logic rather than duplicating net-worth-history query behavior
- Keep existing `reports balances-aggregate`, `reports balances-category`, and `reports networth-history` commands available and behaviorally unchanged

Not included in this phase:

- Migration of `reports networth-history` onto the shared history aggregation core
- Migration of `reports balances-category` onto the shared aggregation core
- New aggregation dimensions beyond `category`, `side`, `institution`, `currency`, and `tag`
- Currency conversion or exchange-rate-based reporting
- New CSV import/export behavior
- Synthetic zero rows for months with no matching balances
- A broader report navigation redesign or TUI-specific report surface

### Report Command Surface

This phase adds one new report command:

- `reports balances-aggregate-history`

Supported options:

| Option | Type | Default | Notes |
|-------|------|---------|-------|
| `--start-month` | `YYYY-MM` | Prompt when omitted | Inclusive lower bound |
| `--end-month` | `YYYY-MM` | Prompt when omitted | Inclusive upper bound |
| `--dimension` | `category \| side \| institution \| currency \| tag` | Prompt when omitted | One grouping dimension only |
| `--currency` | `str` | `None` | Optional explicit currency filter |
| `--status-scope` | `active \| all` | `active` | Advanced opt-in for inactive inclusion |

CLI expectations for this phase:

- The command is additive and does not replace any existing report command.
- The command may run fully from flags, fully interactively, or as a hybrid of both.
- Missing range inputs use the existing reporting-style month selection pattern rather than introducing a new date-entry style.
- Missing `dimension` uses one explicit prompt listing the supported aggregation dimensions.
- `status_scope` defaults to `active` and is not routinely prompted for in the interactive flow.
- The command remains presenter-driven rather than embedding direct console logic in the use case.

### History Aggregation Request Shape

This phase introduces one shared history aggregation request below the CLI layer.

Required public/interface additions:

- `HistoryAggregationRequest`
- `HistoryAggregationRow`
- `HistoryAggregationResult`
- One application use case that accepts a `HistoryAggregationRequest`
- One shared reporting-query port method that supports the same request shape

The shared history aggregation request includes:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `start_month` | `Month` | Required | Inclusive range start |
| `end_month` | `Month` | Required | Inclusive range end |
| `dimension` | `AggregationDimension` | Required | One grouping dimension per request |
| `currency_code` | `str \| None` | Optional | Required only when non-`currency` aggregation would otherwise span multiple currencies across the range |
| `status_scope` | `AccountStatusScope` | Defaults to `ACTIVE` | Allows explicit inclusion of inactive accounts |

Request rules:

- The selected range is inclusive of both `start_month` and `end_month`.
- `start_month` must be less than or equal to `end_month`.
- Exactly one aggregation dimension is requested at a time.
- `status_scope=ACTIVE` includes only active accounts.
- `status_scope=ALL` includes active and inactive accounts.
- `currency` aggregation may omit `currency_code`.
- Non-`currency` aggregation may omit `currency_code` only when all included balances for the selected range already belong to one currency.
- If non-`currency` aggregation would combine multiple currencies across the selected range without an explicit `currency_code`, the use case must fail with clear validation-style feedback instead of producing invalid totals.

### History Aggregation Result Shape

The shared history aggregation result includes:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `start_month` | `Month` | Required | Echoes the requested start month |
| `end_month` | `Month` | Required | Echoes the requested end month |
| `dimension` | `AggregationDimension` | Required | Echoes the requested dimension |
| `currency_code` | `str \| None` | Derived | Resolved currency for non-`currency` requests when known; `None` for multi-currency `currency` aggregation |
| `status_scope` | `AccountStatusScope` | Required | Echoes the applied scope |
| `rows` | `list[HistoryAggregationRow]` | Ordered | Grouped totals for the requested history range |

Each row includes:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `month` | `Month` | Required | Month represented by the grouped total |
| `group_key` | `str` | Required, stable within the dimension | Internal grouping identifier for later CLI and compatibility reuse |
| `label` | `str` | Required | User-facing group label |
| `amount` | `int` | Required | Integer smallest-unit sum |
| `currency_code` | `str` | Required | Currency represented by the amount |

Result rules:

- Months are ordered chronologically ascending.
- Rows within each month follow the same deterministic grouping order already defined for single-month aggregation.
- Months with no matching grouped rows are omitted from the result rather than represented as synthetic zero rows.

### Grouping Semantics

History aggregation uses the same grouping semantics as the single-month aggregation core, applied independently within each month in the selected range.

Required behavior:

- `category` groups by account category name.
- `side` groups by category side with `asset` before `liability`.
- `institution` groups by account institution and includes the `Unassigned` bucket when applicable.
- `currency` groups by account currency code without cross-currency summation.
- `tag` groups by account tag and includes the `Untagged` bucket when applicable.
- Multi-tag accounts contribute their full balance to every assigned tag group within the month being aggregated.

### Mixed-Currency Behavior

This phase mirrors the mixed-currency rules from Phase 17, but applies them across the full selected range.

Required behavior:

- If `--currency` is provided, the command uses it directly.
- If the command is running interactively and the selected range and status scope contain multiple currencies for a non-`currency` aggregation, the workflow prompts the user to choose one currency before running the report.
- The interactive currency prompt uses explicit available currency choices derived from the selected range and status scope.
- If the command is being run without prompt fallback and a mixed-currency non-`currency` request lacks `--currency`, the command fails with clear validation-style feedback telling the user to provide `--currency`.
- The CLI wording must refer to the CLI option name `--currency`, not an internal DTO field name.

### Output And Presentation

This phase introduces one dedicated grouped-history presentation flow.

Required output behavior:

- The workflow shows a report header for the new history aggregated report command.
- The report output includes one long grouped history table and does not also show the legacy net worth summary, total-change summary, account list, or per-month sectioned output.
- The grouped history table includes `Month`, the selected aggregation dimension as the second column label, and `Amount`.
- For non-`currency` aggregation, the resolved report currency is shown in the header or table title context rather than duplicated in every row.
- For `currency` aggregation, each currency remains distinct in the grouped rows and no single report currency is implied.
- Row ordering follows chronological month order first, then the deterministic grouping order returned by the shared aggregation layer.
- Group labels such as `Unassigned` and `Untagged` are rendered exactly as returned by the shared aggregation result.

### Empty And Error Behavior

This phase makes empty and invalid history-report outcomes explicit at the CLI layer.

Required behavior:

- A valid request with no matching balances remains a successful workflow outcome.
- Empty results show a clear no-data message and do not render an empty table.
- Invalid month input uses the existing reporting-style validation feedback.
- A reversed range where `start_month > end_month` is rejected clearly before the shared aggregation request is executed.
- Unsupported or malformed dimension input is rejected clearly before the shared aggregation request is executed.
- Mixed-currency non-`currency` requests without an explicit or interactively selected currency are rejected clearly instead of producing invalid totals.
- Quitting during interactive month, dimension, or currency selection exits the workflow cleanly without partial output.

## Decisions

### Decisions Locked In For This Phase

- Phase 18 adds one new additive command: `reports balances-aggregate-history`.
- The new command uses a hybrid input model: explicit flags when supplied, interactive prompts for missing required inputs.
- The history range is inclusive of both `start_month` and `end_month`.
- `status_scope` remains an optional advanced flag and defaults to `active`.
- The new CLI workflow wraps a shared history aggregation use case rather than introducing bespoke report query logic.
- Mixed-currency non-`currency` requests are resolved through an interactive currency choice when prompting is available, or a clear `--currency` validation error when it is not.
- The new report output is conservative: one header and one long grouped history table.
- Empty valid results are user-visible but not treated as errors.
- Existing `reports balances-aggregate`, `reports balances-category`, and `reports networth-history` commands remain unchanged in this phase.

### Decisions Explicitly Deferred

- Converging `reports networth-history` onto the shared aggregation core
- Converging `reports balances-category` onto the shared aggregation core
- Additional report filters beyond month range, dimension, currency, and status scope
- Automatic currency conversion or exchange-rate-driven reporting
- Breaking changes to existing report command names or output contracts
- Gap-filling behavior that synthesizes zero rows for missing months
- TUI-specific reporting behavior

## Context

This spec should be interpreted through `specs/mission.md`, `specs/roadmap.md`, `specs/tech-stack.md`, `specs/stakeholder-input.md`, and the earlier aggregation phases.

Implementation context for this phase:

- Phase 16 introduced the shared single-month aggregation request, result, and reporting-query/use-case core beneath the CLI.
- Phase 17 introduced one additive grouped single-month CLI report and established the hybrid flag-plus-prompt interaction pattern that this phase should reuse.
- The current CLI still has the legacy `reports networth-history` command, and that command remains a compatibility surface during this phase.
- The current reporting repository and DTO surface do not yet define shared range-based aggregation contracts, so this phase must add explicit history request and result types rather than overloading single-month types.
- The product remains CLI-first, local-first, and monthly-snapshot-based, so report ergonomics should favor explicit prompts and readable output over compact but ambiguous flags alone.

Tone and implementation expectations:

- Use precise CLI-first terminology centered on start month, end month, dimension, currency, and grouped history rows.
- Prefer explicit validation and obvious prompt flows over implicit fallback behavior.
- Keep the report output readable and conservative for the first dedicated history aggregation command.
- Keep the phase independently shippable so Phase 19 compatibility convergence can build on it without reworking the command contract.
