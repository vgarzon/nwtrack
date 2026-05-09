# Phase 9 Requirements: Spec And Domain Shape Alignment

## Scope

This phase defines the shared terminology and spec baseline for institutions, tags, and generalized balance aggregation before implementation begins.

Included in this phase:

- Document the baseline domain shape for `Institution` and `Tag`
- Define the initial relationship of institutions and tags to `Account`
- Standardize the reporting terms that later phases will use
- Record compatibility and migration expectations that should shape later implementation
- Define the expectation that each later feature phase includes explicit testing and quality-check requirements
- Keep institutions and tags optional on accounts in the initial rollout

Not included in this phase:

- Database migrations or schema implementation
- CLI command implementation
- Account workflow rewiring
- Aggregated reporting command behavior beyond terminology and scope boundaries
- Final validation rules for later institution-required accounts

### Institution

An institution is a financial institution where an account is held.

Initial institution baseline:

- `Institution` is first-class reference data, not an unchecked account text field.
- The baseline institution shape is intentionally small: `id`, `name`, and optional `description`.
- Institution `name` must be unique so accounts can reference one unambiguous institution record.
- Additional institution attributes remain out of scope until a later feature phase explicitly adds them.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `int` | Primary key, unique | Internal identifier |
| `name` | `string` | Required, short label, unique | User-facing institution label |
| `description` | `string` | Optional free-text | Supplemental context only |

Initial account relationship:

- An account may reference zero or one institution in the initial rollout.
- Institution assignment remains optional during the early institution phases.
- Existing accounts must remain valid without an institution until a later migration phase explicitly changes that rule.
- The initial account model should use an optional institution reference rather than duplicating institution names on accounts.

Initial migration posture:

- Existing accounts are not reassigned automatically during this phase.
- Institutions will be attached manually to active accounts during later implementation phases.
- Schema and workflow changes must preserve current accounts that do not yet have an institution.

### Tag

A tag is a reusable account label used for grouping and reporting.

Initial tag baseline:

- `Tag` is first-class reference data, not an unchecked multi-value text field on accounts.
- The baseline tag shape is intentionally small: `id`, `name`, and optional `description`.
- Tag `name` must be unique so accounts can reference unambiguous reusable tag records.
- Additional tag attributes remain out of scope until a later feature phase explicitly adds them.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `int` | Primary key, unique | Internal identifier |
| `name` | `string` | Required, short label, unique | User-facing tag label |
| `description` | `string` | Optional free-text | Supplemental context only |

Initial account relationship:

- An account may reference zero, one, or many tags.
- Tags may be shared across multiple accounts.
- Tags are user-managed reference data, even though they support flexible grouping.
- The initial account model should represent tag assignment through explicit associations rather than duplicated free-form account text.

Initial migration posture:

- Existing accounts remain valid with zero tags during the initial rollout.
- Tags will be attached manually to active accounts during later implementation phases.
- Schema and workflow changes must preserve current accounts that do not yet have any tags.

### Reporting Terms

This phase does not define the full aggregated reporting feature. It defines the vocabulary that later reporting phases should use.

- Aggregation dimension: the account attribute used to group balances, such as category, side, institution, currency, or tag.
- Single-month aggregation: grouped balances for one `YYYY-MM` month.
- History aggregation: grouped balances across a start and end `YYYY-MM` range.
- Compatibility reporting: existing user-facing report commands that should converge on the shared aggregation model where practical.

Reporting boundary decisions for this phase:

- Later reporting phases should describe new reporting features in terms of aggregation dimensions and aggregation windows, not as isolated bespoke report types.
- Existing net worth and category report commands should be treated as compatibility reporting surfaces over the same shared aggregation model.
- Shared reporting logic should converge below the CLI layer so old and new commands can reuse the same aggregation primitives.

Reporting decisions explicitly deferred:

- CLI command names, flags, prompts, and output formatting for future aggregation commands
- Exact tag aggregation semantics for accounts with multiple tags
- The order in which compatibility commands move onto the shared aggregation model
- CSV import/export implications of future reporting changes

Reporting implementation details, CLI flags, output formatting, migration sequencing, and tag aggregation edge-case semantics remain for later phases.

## Decisions

### Decisions Locked In For This Phase

- `Institution` and `Tag` are first-class entities, not ad hoc text fields on accounts.
- Both entities use the same initial baseline field shape: `id`, `name`, and optional `description`.
- Institution assignment is optional during the first institution phases.
- Tag assignment is optional and supports many-to-many account associations.
- Institutions and tags will be added manually to active accounts during the rollout to protect data integrity and avoid disruptive bulk backfills.
- Reporting work is deferred, but all later reporting specs should use the standardized aggregation vocabulary from this document.
- Existing report commands are compatibility reporting surfaces and should converge on one shared aggregation model where practical.
- Later feature specs must define the tests, assertions, and quality checks required for the feature, not rely only on generic repository-level gates.

### Decisions Explicitly Deferred

- Exact persistence and migration mechanics
- CLI command names and prompt flows
- Detailed validation and deletion semantics for institution and tag management
- CSV import/export changes
- Detailed aggregation semantics for accounts with multiple tags
- Future aggregation CLI command design and output details
- The exact cutover rules for making institutions mandatory later

## Context

This spec should be interpreted through the project constitution in `specs/mission.md` and `specs/tech-stack.md`.

Context for later implementation:

- `nwtrack` is CLI-first and local-first.
- SQLite, SQLAlchemy, Typer, Rich, Pytest, Ruff, and mypy remain the default stack.
- Monthly snapshot tracking stays the permanent core model.
- Specs should preserve low-friction monthly updates over administrative complexity.
- New account attributes should support reporting by composition rather than creating separate reporting data models.
- Every implementation phase should name the automated tests, manual checks, and quality gates needed to validate the change.

Tone and documentation expectations:

- Use precise CLI-oriented language.
- Prefer compatibility-preserving behavior unless a later feature spec explicitly justifies a break.
- Keep follow-on phases small and independently shippable.
- Call out open questions rather than silently deciding them when later phases need sharper behavior.
