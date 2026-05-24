# nwtrack Roadmap

## Purpose

This document defines the current best known implementation order for upcoming work in very small phases.

The roadmap should optimize for:

1. Safe schema evolution
2. Compatibility with existing CLI workflows where practical
3. Thin vertical slices that keep the product usable at each step
4. Convergence toward a generalized reporting model

## Current Baseline

`nwtrack` already has:

- A local SQLite-backed CLI application
- SQLAlchemy-based persistence
- Layered domain, application, infrastructure, and CLI entrypoints
- Interactive workflows for accounts, categories, balances, roll-forward, deletion, export, reports, and transfers
- Presenter-based separation across much of the interactive CLI surface
- Automated tests, linting, and type checking integrated into the development workflow

## Planned Phases

### [X] Phase 9: Spec And Domain Shape Alignment

Goal:
Define the feature specs and align shared terminology around institutions, tags, and generalized balance aggregation.

Expected outcomes:

- Feature specs exist for institution management, tag management, and aggregated balance reporting
- Shared terminology is standardized around account attributes and aggregation dimensions
- Compatibility expectations for existing reporting commands are written down before implementation

### [X] Phase 10: Institution Schema Foundation

Goal:
Add first-class institution persistence without forcing immediate account reassignment.

Expected outcomes:

- `Institution` entity, ORM mapping, repository support, and tests exist
- Accounts can reference an optional institution
- Database migration path preserves existing account records
- CSV import/export behavior is updated or explicitly deferred in the feature spec

### [X] Phase 11: Institution CLI CRUD

Goal:
Make institutions user-manageable from the CLI before deeper account workflow changes.

Expected outcomes:

- CLI commands exist to create, list, update, and delete institutions
- Validation prevents ambiguous or unsafe institution operations
- Presenter and prompt flows match existing account/category administration patterns

### [X] Phase 12: Account Workflows With Optional Institution

Goal:
Thread institution support through account creation, editing, listing, and fetch flows.

Expected outcomes:

- Account create/update commands can select an institution
- Account list and detail-oriented outputs surface institution consistently
- Existing accounts remain valid without an institution during this phase
- Tests cover interactive and non-interactive institution assignment paths

### [X] Phase 12b: Interactive Balance Creation

Goal:
Add an interactive CLI command for creating one missing balance entry without changing the existing balance update and delete workflows.

Expected outcomes:

- A `balances create` command exists for one-off balance entry creation
- The workflow can create a balance for one active account and one `YYYY-MM` month
- Duplicate balance entries for the same account and month are rejected with clear validation
- Existing balance update, delete, roll-forward, and transfer workflows remain unchanged during this phase

### [X] Phase 13: Tag Schema Foundation

Goal:
Add controlled tags and account-to-tag associations in the data model.

Expected outcomes:

- `Tag` entity, ORM mapping, association table, repository support, and tests exist
- Accounts can reference zero, one, or many tags by ID
- Database migration path preserves existing account and balance records
- CSV import/export behavior is updated or explicitly deferred in the feature spec

### [X] Phase 14: Tag CLI CRUD

Goal:
Make tags independently manageable before wiring them into account workflows.

Expected outcomes:

- CLI commands exist to create, list, update, and delete tags
- Validation preserves controlled-label behavior
- Deletion and rename semantics are defined and tested

### [X] Phase 15: Account Workflows With Tags

Goal:
Thread tag assignment through account management in a way that remains efficient for monthly workflows.

Expected outcomes:

- Account create/update commands can attach and detach tags
- Account listing and selection flows can surface tags where useful
- Account fetch/read models expose tags for reporting and presentation
- Tests cover empty, single-tag, and multi-tag account cases

### [X] Phase 16: Shared Aggregation Query Layer

Goal:
Build one reporting core for balance aggregation by account attributes.

Expected outcomes:

- Shared query/use-case support exists for aggregation by category, side, institution, currency, and tag
- Single-month aggregation is implemented first
- Tag aggregation semantics for multi-tag accounts are explicitly defined in the feature spec and tests
- Report outputs remain CLI-oriented

### [X] Phase 17: New Single-Month Aggregated Balance Report

Goal:
Expose the generalized single-month report through a dedicated CLI command.

Expected outcomes:

- A CLI report command accepts a month and one aggregation dimension
- Rich output presents grouped balances clearly
- Existing net worth and category reporting commands continue to work during this phase

### [X] Phase 18: History Aggregated Balance Report

Goal:
Extend the shared aggregation model to month history between two `YYYY-MM` values.

Expected outcomes:

- A CLI report command accepts start month, end month, and one aggregation dimension
- Output shows per-month grouped balances over the requested range
- History reporting reuses the shared aggregation core rather than duplicating query logic

### [X] Phase 19: Compatibility Convergence

Goal:
Move older reporting commands onto the generalized reporting core while preserving user-facing behavior where practical.

Expected outcomes:

- Existing net worth reporting uses aggregation-by-side internally
- Existing category balance reporting uses aggregation-by-category internally
- CLI output changes are limited to what is necessary for consistency or new data requirements
- Compatibility differences are documented in release notes or feature specs
- Mixed-currency compatibility reporting fails clearly until explicit conversion-based reporting exists

### [X] Phase 20: Networth History All-Account Default

Goal:
Fix inaccurate historical networth reports by changing the default account filter from active-only to all accounts, and expose an opt-in flag for the previous active-only behavior.

Background:
`nwtrack reports networth-history` currently applies the current account status to all historical months, so accounts that were active in the past but are now inactive or closed are silently excluded from every historical data point.  Inactive and closed accounts should carry a zero balance, so including all accounts in historical aggregation produces a more accurate picture of networth over time without requiring schema changes.

Expected outcomes:

- `nwtrack reports networth-history` defaults to `AccountStatusScope.ALL`, including balances from accounts regardless of their current status
- The command accepts an `--active-only` flag that restores the previous `AccountStatusScope.ACTIVE` behavior for users who want to filter on current status
- `NetworthHistoryReport.run()` and its `main()` entry point accept and propagate a `status_scope` parameter so the scope is injectable and testable
- The CLI command wires `--active-only` to `status_scope=AccountStatusScope.ACTIVE` and passes the resolved scope through to the use case
- Tests cover the default all-account path and the `--active-only` opt-in path
- Existing `balances-aggregate` and `balances-aggregate-history` commands are unchanged; they already expose `--status-scope` directly

Validation:

- `pytest` passes with tests for both status scope paths on the networth history use case
- `ruff` and `mypy` pass
- Manual verification: running `nwtrack reports networth-history` against a database with inactive accounts produces totals that include those accounts; running with `--active-only` excludes them

### [X] Phase 21: Institution Requirement Migration Plan

Goal:
Prepare the product to make institutions required on accounts in a later change without disrupting current users.

Expected outcomes:

- A migration strategy exists for accounts that still lack institutions
- CLI and validation rules can identify and remediate missing institutions
- The spec defines the cutover criteria for making institution assignment mandatory

### [X] Phase 22: CSV Export Coverage For Institutions And Tags

Goal:
Extend the existing CSV export workflow so exported table sets include the newer account classification tables needed for data portability.

Expected outcomes:

- The existing export CSV command and use case include `institutions` and `tags` in export output
- Exported CSV table sets are defined to remain consistent with the supported import format
- CSV export behavior moves closer to full local backup and recovery for the current data model

### [ ] Phase 23: Account Status History

Goal:
Record account status changes over time so that historical reports can apply each account's status as of each reporting month rather than projecting the current status backward.

Background:
Phase 20 improves historical accuracy by including all accounts unconditionally, which works as long as inactive accounts carry zero balances.  The root cause remains: the data model has no record of when an account's status changed.  This phase closes that gap with a dedicated status-history table and updates aggregation queries to join against it per month.

Expected outcomes:

- A new `account_status_history` table exists with columns `id`, `account_id`, `status`, and `effective_month` (`YYYY-MM`), where each row records the status that became effective at a given month
- A database migration adds the table and seeds one initial row per account using the account's current status and a representative effective month derived from the account's earliest balance record or creation date
- `AccountRepository` (or a dedicated status-history repository) exposes methods to insert status-history rows and look up an account's effective status for a given month
- Aggregation queries in `ReportingQueries` can join `account_status_history` to filter by effective status at each balance month, replacing the current join on `Account.status`
- `AccountStatusScope` semantics are updated or extended so reporting layers can request historically-accurate status filtering
- `nwtrack reports networth-history` and aggregated history reports use the per-month effective status when available
- The seeding migration logic and its assumptions are documented in the feature spec
- Tests cover: status-history inserts, effective-status lookup at a given month, and history aggregation filtered by historical status across a multi-month range
- `ruff`, `mypy`, and `pytest` pass
- CSV export and import include `account_status_history` in supported table sets, or the feature spec explicitly defers that to a follow-on phase

### [X] Phase 24: CSV Import Command And Round-Trip Foundation

Goal:
Add a first-class CLI import workflow for CSV table data and align import behavior with the current schema and portability goals.

Expected outcomes:

- A new `import` CLI command group exists with a `tables-csv` command
- The CSV import use case updates the current initialization/import path to include `institutions` and `tags`
- Import can create the database file and required schema when starting from an empty or missing database
- CSV import behavior is idempotent, with exact semantics defined in the feature spec
- Export/import CSV round trips preserve the same database data for supported tables

### [X] Phase 25: CSV Presenter Protocol Migration

Goal:
Complete the presenter protocol migration for the two remaining use cases that still performed
direct console I/O, decoupling all interactive use cases from the presentation layer before
TUI development begins.

Expected outcomes:

- `ImportTablesCSVPresenter` and `ExportTablesCSVPresenter` Protocol interfaces defined in
  `application/ports/presentation.py`
- `RichImportTablesCSVPresenter` and `RichExportTablesCSVPresenter` adapters implemented in
  `entrypoints/cli/adapters/csv_presenters.py`
- `import_tables_csv` and `export_tables_csv` use cases refactored to accept presenter via
  constructor; direct Rich imports removed from both use case modules
- All interactive use cases are now fully decoupled from the presentation layer
- Tests updated to use mock presenters; presenter interaction assertions added for all paths

### [ ] Phase 26: Reporting UX Options

Goal:
Improve aggregated reporting ergonomics with alternative history layouts and export-friendly output.

Expected outcomes:

- History aggregated balance reporting can render either long or wide table output
- Non-interactive aggregated history reporting can emit CSV output for downstream analysis
- Output-format options are defined in a way that preserves current default behavior unless the user opts in

### [ ] Phase 27: Single-Currency Conversion Reporting

Goal:
Add conversion-backed reporting so aggregated views can be rendered in one explicit reporting currency instead of failing on mixed-currency totals.

Expected outcomes:

- Reporting can convert mixed-currency balances into one explicit reporting currency before aggregation
- USD is supported as the initial consolidated reporting currency
- Conversion rules and required exchange-rate inputs are defined clearly for reporting workflows
- Compatibility and aggregated report commands can converge on accounting-correct single-currency output where conversion data exists

## Planning Rules

- Keep phases small enough to land independently.
- Prefer schema-first changes before broad CLI rewiring.
- Preserve existing command behavior where practical until replacement paths are proven.
- Route new reporting work through shared aggregation primitives instead of adding more bespoke report logic.
- Prefer accounting-correct single-currency output; when conversion support is not available, fail clearly instead of summing mixed currencies.
- Treat testing and quality checks as part of phase validation, and document them explicitly in each phase spec.
- Update this roadmap when feature specs materially change implementation order.
