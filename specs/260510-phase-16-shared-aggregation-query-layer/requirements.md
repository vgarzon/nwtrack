# Phase 16 Requirements: Shared Aggregation Query Layer

## Scope

This phase introduces one shared single-month aggregation core for reporting by account attributes without yet adding a new report command or moving existing compatibility commands onto that core.

Included in this phase:

- Add shared application-level request and result DTOs for single-month aggregation
- Add one generic aggregation dimension enum covering `category`, `side`, `institution`, `currency`, and `tag`
- Add one shared use case that executes a single-month aggregation request
- Add one shared reporting-query interface and SQLAlchemy implementation beneath that use case
- Support account-status scoping with `active` as the default and `all` as an explicit opt-in
- Define and test aggregation semantics for unassigned institutions, untagged accounts, multi-tag accounts, and mixed-currency protection
- Keep the output CLI-oriented in the sense that later CLI commands can present it directly, while keeping Phase 16 logic below the CLI layer

Not included in this phase:

- A new end-user CLI report command
- Presenter or Rich rendering changes for a new aggregated report
- History aggregation across a month range
- Migration of existing `reports balances-category` or `reports networth-history` onto the shared core
- Automatic currency conversion or exchange-rate-based aggregation
- CSV import/export changes

### Reporting Surface In Scope

This phase adds a shared reporting core below the CLI layer.

Required public/interface additions:

- `AggregationDimension` enum with `CATEGORY`, `SIDE`, `INSTITUTION`, `CURRENCY`, and `TAG`
- `AccountStatusScope` enum with `ACTIVE` and `ALL`
- `SingleMonthAggregationRequest` DTO
- `SingleMonthAggregationGroup` DTO
- `SingleMonthAggregationResult` DTO
- One application use case that accepts a `SingleMonthAggregationRequest`
- One shared reporting-query port that supports the same request shape

CLI expectations for this phase:

- Existing report commands remain available and behaviorally unchanged.
- The shared aggregation layer must be usable by later CLI phases without requiring query rewrites.
- No new command name, prompt flow, flags, or Rich table layout is defined in this phase.

### Aggregation Request Shape

The shared single-month aggregation request includes:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `month` | `Month` | Required | One `YYYY-MM` month only |
| `dimension` | `AggregationDimension` | Required | One grouping dimension per request |
| `currency_code` | `str \| None` | Optional | Required only when non-`currency` aggregation would otherwise span multiple currencies |
| `status_scope` | `AccountStatusScope` | Defaults to `ACTIVE` | Allows explicit inclusion of inactive accounts |

Request rules:

- Exactly one aggregation dimension is requested at a time.
- `status_scope=ACTIVE` includes only active accounts.
- `status_scope=ALL` includes active and inactive accounts.
- `currency` aggregation may omit `currency_code`.
- Non-`currency` aggregation may omit `currency_code` only when all included balances for the selected month already belong to one currency.
- If non-`currency` aggregation would combine multiple currencies without an explicit `currency_code`, the use case must fail with clear validation-style feedback instead of producing invalid totals.

### Aggregation Result Shape

The shared single-month aggregation result includes:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `month` | `Month` | Required | Echoes the requested month |
| `dimension` | `AggregationDimension` | Required | Echoes the requested dimension |
| `currency_code` | `str \| None` | Derived | Resolved currency for non-`currency` requests when known; `None` for multi-currency `currency` aggregation |
| `status_scope` | `AccountStatusScope` | Required | Echoes the applied scope |
| `groups` | `list[SingleMonthAggregationGroup]` | Ordered | Grouped totals for the request |

Each group includes:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `group_key` | `str` | Required, stable within the dimension | Internal grouping identifier for later CLI and compatibility reuse |
| `label` | `str` | Required | User-facing group label |
| `amount` | `int` | Required | Integer smallest-unit sum |
| `currency_code` | `str` | Required | Currency represented by the amount |

### Grouping Semantics

#### Category

- Group by account category name.
- Category aggregation uses the account attribute already associated with each balance through its account.
- Output order is ascending by category name.

#### Side

- Group by category side.
- The only valid labels are `asset` and `liability`.
- Output order is `asset` first, then `liability`.

#### Institution

- Group by institution identity for the account linked to each balance.
- Accounts with no institution assigned are included in an explicit unassigned bucket.
- The unassigned bucket label is `Unassigned`.
- Assigned institutions sort by ascending institution name, with the unassigned bucket last.

#### Currency

- Group by account currency code.
- `currency` aggregation never combines different currencies into one total.
- Output order is ascending by currency code.

#### Tag

- Group by tag identity for the account linked to each balance.
- Accounts with zero tags are included in an explicit untagged bucket.
- The untagged bucket label is `Untagged`.
- Assigned tags sort by ascending normalized stored tag name, with the untagged bucket last.

### Multi-Tag Semantics

This phase locks the reporting semantics for accounts that have more than one tag.

- Tag aggregation is membership-based, not partition-based.
- One account balance contributes its full amount to every assigned tag group.
- The same account balance is counted once in the untagged bucket only when the account has zero tags.
- Tag-group totals therefore are not expected to sum to the same total as category, side, institution, or currency aggregation for the same month.

### Empty And Missing Data Behavior

- A valid request with no matching balances returns a successful result with an empty `groups` list.
- This phase does not define CLI wording for empty results.
- Missing balances for one month do not imply a validation error by themselves.
- Invalid aggregation requests fail before returning grouped totals.

## Decisions

### Decisions Locked In For This Phase

- Phase 16 is limited to a shared single-month aggregation core below the CLI layer.
- The primary public shape is one generic use case plus shared DTOs, not a presenter-ready report workflow.
- The shared API is one dimensioned aggregation interface rather than one public method per dimension.
- Account-status filtering is part of the shared request shape, with active-only as the default.
- Non-`currency` aggregation must not produce raw mixed-currency sums.
- Institution aggregation includes an explicit unassigned bucket.
- Tag aggregation includes an explicit untagged bucket.
- Multi-tag accounts contribute their full balance to every assigned tag group.
- Result ordering must be deterministic so later CLI phases and compatibility layers can rely on it.
- Existing report commands remain compatibility surfaces outside this phase's implementation scope.

### Decisions Explicitly Deferred

- CLI command name, flags, prompt flow, and Rich rendering for the new single-month aggregated report
- History aggregation request and result shapes
- Migration of existing report commands onto the shared aggregation core
- Any currency conversion behavior using exchange rates
- CSV implications of the new reporting core
- Additional report-specific filtering beyond month, dimension, currency, and status scope

## Context

This spec should be interpreted through `specs/mission.md`, `specs/roadmap.md`, `specs/tech-stack.md`, and the reporting vocabulary set in `specs/260508-spec-and-domain-shape-alignment/requirements.md`.

Implementation context for this phase:

- The current codebase already has category-only reporting queries and separate net worth aggregation logic.
- This phase should replace narrow reporting assumptions with one shared single-month aggregation path without prematurely redesigning the CLI.
- The product remains local-first, CLI-first, and monthly-snapshot-based.
- Balances remain stored as integer smallest-unit amounts, so the aggregation layer must preserve accounting correctness by preventing invalid mixed-currency totals.
- Existing report commands should remain usable while Phase 17 and later phases build the new command surface and compatibility convergence on top of this core.

Tone and implementation expectations:

- Use precise CLI and accounting language.
- Prefer explicit validation over ambiguous fallback behavior.
- Keep the phase independently shippable and narrow enough that Phase 17 can focus on the new single-month report command.
- Keep shared reporting logic below the CLI layer so later commands reuse one source of truth.
