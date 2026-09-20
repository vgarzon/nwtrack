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

### [X] Phase 23: CSV Import Command And Round-Trip Foundation

Goal:
Add a first-class CLI import workflow for CSV table data and align import behavior with the current schema and portability goals.

Expected outcomes:

- A new `import` CLI command group exists with a `tables-csv` command
- The CSV import use case updates the current initialization/import path to include `institutions` and `tags`
- Import can create the database file and required schema when starting from an empty or missing database
- CSV import behavior is idempotent, with exact semantics defined in the feature spec
- Export/import CSV round trips preserve the same database data for supported tables

### [X] Phase 24: CSV Presenter Protocol Migration

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

### [X] Phase 25: TUI Prototype — Textual Balance Update Screen

Goal:
Validate that Textual can drive the balance update workflow against a real database, prove (or
characterize) the adapter-swap pattern in practice, and establish the foundation for the full TUI
buildout.

Background:
Step 1 of the TUI transition (presenter protocol migration) is complete as of Phase 24. This phase
executes Step 2: build one Textual screen end-to-end to surface real constraints before committing
to the full transition design. See `specs/tui-scope.md` and
`specs/260523-phase-25-tui-textual-balance-prototype/` for full scope and plan.

Expected outcomes:

- `textual` added as a project dependency
- `nwtrack tui launch` entry point launches a Textual application
- A balance update screen presents active accounts for the most recent month in a scrollable
  editable grid; editing a row persists the change to the real database
- Net worth for the selected month is displayed and updated after each balance change
- A separate TUI composition root wires `FetchService` and `UnitOfWork` without modifying the
  CLI composition root
- The existing `nwtrack balances update` CLI command is unmodified and fully functional
- The Protocol compatibility tension (synchronous `BalanceUpdatePresenter` vs. Textual's async
  model) is investigated and the finding is documented in the spec
- `ruff`, `mypy`, and `pytest` pass

### [X] Phase 26: TUI Screen Model Design

Goal:
Design the full TUI screen hierarchy, navigation model, and interaction conventions before
incremental screen buildout begins. This is a design-only phase; no production code.

Background:
The Phase 25 prototype validated that Textual can drive the balance workflow and surfaced the
screen-owned workflow pattern as the correct implementation approach. Phase 26 answers the
structural questions the prototype deliberately left open: how users navigate between workflows,
what the home entry point looks like, and how the month selection UX works.

Expected outcomes:

- A screen inventory document listing every planned TUI screen, its primary workflow, and the
  navigation paths that lead to and from it
- ASCII wireframes for the home menu and the balance update screen (with month selection)
- Keyboard navigation conventions confirmed and documented
- The edit input UX decision settled: inline cell, overlay modal, or below-table (current
  prototype approach) — with rationale
- Open design questions from `specs/tui-prototype.md` (month selection, nav model, input UX)
  are answered in the design document
- No new implementation; the prototype code in Phase 25 remains the baseline

Validation:

- Design document and wireframes exist in `specs/` and are reviewed before Phase 27 begins
- The document answers all three "Recommended Starting Point" questions from `specs/tui-prototype.md`

### [X] Phase 27: TUI Month Selection and Balance Screen Polish

Goal:
Add month selection UX to the balance update screen and address the deferred items from the
prototype that affect daily usability.

Background:
The Phase 25 prototype hardcodes the most recent available month. Month selection is the most
immediate gap before the balance update screen is useful for real monthly workflows.

Expected outcomes:

- The balance update screen allows the user to navigate to a different month (mechanism per
  Phase 26 design — modal picker, sidebar, or screen push)
- The selected month is reflected in the screen header or subtitle
- Invalid amount input shows an error message rather than silently closing the edit input
- The `reactive[int]` net_worth field is either wired to drive the label reactively or removed
  in favor of the current imperative `_refresh_networth()` approach — one or the other, not both
- `ruff`, `mypy`, and `pytest` pass

### [X] Phase 28: TUI Home Screen and Navigation Shell

Goal:
Add a home menu screen and a screen stack so the TUI has a proper entry point and navigation
hierarchy rather than launching directly into the balance update screen.

Background:
`tui-scope.md` defines the navigation model as a screen stack: home screen presents a workflow
menu; selecting an item pushes the workflow screen; Escape pops back to home. This phase
implements that skeleton.

Expected outcomes:

- `NWTrackApp.on_mount` pushes a home screen rather than `BalanceUpdateScreen` directly
- The home screen presents at minimum: Balances, Reports (placeholder), Accounts (placeholder)
- Selecting Balances navigates to the balance update screen (with month selection from Phase 27)
- Escape from any workflow screen returns to the home screen
- `ruff`, `mypy`, and `pytest` pass

### [X] Phase 29: TUI Report Screens

Goal:
Add TUI screens for the single-month and history aggregated balance reports so the primary
read-only workflows are accessible from the TUI.

Background:
Phases 33 and 34 (Reporting UX Options and Single-Currency Conversion Reporting) define the
reporting model that TUI report screens should surface. Phase 29 may proceed against the current
reporting surface and be updated once those phases land, or it may be deferred until after them.

Expected outcomes:

- A net worth history screen displays the history aggregation report in a scrollable DataTable
- A single-month aggregation screen accepts an aggregation dimension and renders grouped balances
- Report screens are reachable from the home menu and return to home on Escape
- `ruff`, `mypy`, and `pytest` pass

### [X] Phase 30: TUI Account and Administrative Screens

Goal:
Add TUI screens for account listing and management, and for the administrative CRUD workflows
(categories, institutions, tags).

Expected outcomes:

- An account list screen shows all accounts with status, category, institution, and tags
- Account create/edit workflows are accessible from the account list screen
- Category, institution, and tag list and create/edit screens exist under an Admin section
- All screens are reachable from the home menu navigation hierarchy
- `ruff`, `mypy`, and `pytest` pass

### [X] Phase 31: TUI Balance Operations

Goal:
Add TUI screens for balance roll-forward, delete, and transfer so the remaining balance
workflows are accessible from the TUI.

Expected outcomes:

- Roll-forward, delete, and transfer balance operations are accessible from the TUI
- These screens follow the screen-owned workflow pattern established in Phase 25
- `ruff`, `mypy`, and `pytest` pass

### [X] Phase 32: Account Status History

Goal:
Record account status changes over time so that historical reports can apply each account's status as of each reporting month rather than projecting the current status backward.

Background:
Phase 20 improves historical accuracy by including all accounts unconditionally, which works as long as inactive accounts carry zero balances.  The root cause remains: the data model has no record of when an account's status changed.  This phase closes that gap with a dedicated status-history table and updates aggregation queries to join against it per month.

Expected outcomes:

- A new `account_status_history` table exists with columns `id`, `account_id`, `status`, and `effective_month` (`YYYY-MM`), where each row records the status that became effective at a given month
- A dedicated `AccountStatusHistoryRepository` exposes methods to insert status-history rows, look up effective status for a given month, and support CSV hydration
- Initial rows are seeded via `nwtrack admin seed-status-history` (on-demand, not on startup); seeding logic and assumptions are documented in the feature spec
- Account creation inserts an initial `(active, initial_month)` history row atomically, via both CLI and TUI paths
- Account status changes insert a new `(new_status, current_month)` history row atomically, via both CLI (`update_account_info`) and TUI (`AccountsListScreen`)
- `AccountStatusScope.HISTORICAL` applies per-month effective status to all aggregation queries via a correlated subquery with `COALESCE` fallback to `Account.status`
- All CLI `--status-scope` flags accept `historical` as a valid value
- `ruff`, `mypy`, and `pytest` pass (331 tests)
- `account_status_history` is included in CSV export and import

### [X] Phase 33: TUI Status Scope Selector

Goal:
Expose status scope selection in TUI report screens so users can switch between `historical`,
`active`, and `all` filtering without leaving the TUI.

Background:
Phase 32 wired `AccountStatusScope.HISTORICAL` as the new default across all CLI and TUI report
surfaces. TUI screens currently hardcode their scope and offer no user control. This phase adds
a scope selector widget to the net worth history screen and the single-month aggregation screen,
matching the scope control already available on the CLI via `--status-scope`.

Expected outcomes:

- `NetWorthHistoryScreen` exposes a `Select` scope dropdown (Historical / Active / All);
  changing scope refreshes the report in place without resetting pinned start/end dates
- `AggregationScreen` exposes the same `Select` scope dropdown; the existing dimension Select
  and the new scope Select share a single `on_select_changed` handler disambiguated by value type
- Both screens default to `AccountStatusScope.HISTORICAL` (consistent with CLI defaults)
- `NetWorthHistoryScreen` DataTable adds a Delta column (month-over-month net worth change)
  and a Total summary row
- Amount column in `BalanceUpdateScreen` is right-justified
- `ruff`, `mypy`, and `pytest` pass (340 tests)

### [ ] Phase 34 (On Hold): Reporting UX Options

Goal:
Improve aggregated reporting ergonomics with alternative history layouts and export-friendly output.

Expected outcomes:

- History aggregated balance reporting can render either long or wide table output
- Non-interactive aggregated history reporting can emit CSV output for downstream analysis
- Output-format options are defined in a way that preserves current default behavior unless the user opts in

### [ ] Phase 35 (On Hold): Single-Currency Conversion Reporting

Goal:
Add conversion-backed reporting so aggregated views can be rendered in one explicit reporting currency instead of failing on mixed-currency totals.

Expected outcomes:

- Reporting can convert mixed-currency balances into one explicit reporting currency before aggregation
- USD is supported as the initial consolidated reporting currency
- Conversion rules and required exchange-rate inputs are defined clearly for reporting workflows
- Compatibility and aggregated report commands can converge on accounting-correct single-currency output where conversion data exists

### [ ] Phase 36 (On Hold, Optional): CLI Retirement

Goal:
Retire the CLI entry points once the TUI covers the full workflow scope and has been validated
against real usage.

Background:
`tui-scope.md` defines CLI retirement as the final step: the `nwtrack tui` entry point
becomes `nwtrack`. This phase should not begin until all workflows from Phases 27–35 are
complete and have been validated against real data. It is marked optional because the CLI and
TUI may coexist indefinitely if the dual-mode workflow proves useful in practice.

Expected outcomes:

- All Typer command groups and CLI presenter adapters are removed
- `bootstrap/composition.py` CLI-specific registrations are removed or folded into the TUI
  composition root
- `[project.scripts]` in `pyproject.toml` points `nwtrack` at the TUI entry point
- Existing `tests/entrypoints/` CLI tests are removed or migrated to TUI equivalents
- `ruff`, `mypy`, and `pytest` pass with no orphaned CLI references

### [ ] Phase 37 (On Hold, Future): Database Migration Tooling

Goal:
Replace the current hand-rolled `SchemaManager` with a proper migration tool (Alembic or
equivalent) so that schema evolution is versioned, auditable, and reversible.

Background:
The current approach applies compatibility upgrades imperatively in `ensure_current_schema()`.
This works for additive changes (new tables, new nullable columns) but has no concept of
migration versions or rollbacks. As the schema grows and the user base widens, ad-hoc
upgrade code becomes increasingly fragile. Alembic is the standard SQLAlchemy migration
tool and would bring auto-generated migration scripts, version tracking via an `alembic_version`
table, and a clear separation between initial schema creation and incremental upgrades.

Expected outcomes:

- Alembic integrated as a project dependency with a migration environment under `migrations/`
- An initial migration captures the current full schema as a baseline
- `SchemaManager.ensure_current_schema()` delegates to `alembic upgrade head`
- `nwtrack admin seed-status-history` remains available as a data-migration command
  distinct from schema migrations
- The legacy `_ensure_sqlite_legacy_columns` compatibility shim is retired, replaced by
  a versioned Alembic migration
- `ruff`, `mypy`, and `pytest` pass; existing test fixtures continue to create schemas
  via `Base.metadata.create_all` (test isolation is unchanged)

## Reprioritization Note

Phases 34–37 are on hold. Phases 38–41 below take priority as the current active
work. Phases 34–37 remain defined and will resume after 38–41 land, in their
original relative order, unless a future roadmap update says otherwise.

### [X] Phase 38: Single Account Balance History Report

Goal:
Add a report that shows one account's balance history over a month range, with
month-over-month deltas and summary trend statistics, available from both the CLI
and the TUI.

Background:
Existing reporting surfaces aggregate across accounts (by category, side, institution,
currency, or tag). There is no report focused on a single account's own trajectory over
time. Unlike the shared aggregation model in `specs/tech-stack.md`, a single-account
history is not a cross-account grouping, so it is implemented as a dedicated per-account
query rather than routed through the shared aggregation core.

Expected outcomes:

- A new use case computes one account's balance for each month in a start/end `YYYY-MM`
  range, including a month-over-month delta and summary trend stats (min, max, average,
  total change over the range)
- A new CLI report command accepts an account selection and a start/end month range and
  renders the history, deltas, and trend summary
- A new TUI report screen offers the same workflow: account selection, month range input,
  and a scrollable table of balances, deltas, and a trend summary
- The report defaults to `AccountStatusScope.HISTORICAL`, consistent with other report
  surfaces (Phase 32/33); no status-scope selector is required since the report is scoped
  to a single account
- Missing balance months within the selected range are handled explicitly (defined in the
  feature spec) rather than silently skipped
- `ruff`, `mypy`, and `pytest` pass

### [X] Phase 39: TUI Visual Design System

Goal:
Introduce a reusable Textual theme module with dark and light modes and apply consistent
layout and spacing polish across all existing TUI screens.

Background:
TUI screens have accumulated incrementally since Phase 25 without a shared visual design
system. This phase adds one reusable theme/CSS module that all screens reference, so
future screens inherit consistent styling automatically, and revisits existing screens for
layout and spacing polish under the new theme.

Expected outcomes:

- A shared Textual theme module (`entrypoints/tui/theme.py`) defines reusable CSS classes
  (modal chrome, titles, error/hint labels, button rows) and spacing constants, registered
  globally via `NWTrackApp.CSS`; dark/light mode reuses Textual's own built-in theme
  mechanism (`App.theme` / `action_toggle_dark`) rather than a hand-rolled color palette
- All existing TUI screens (home, balances, reports, accounts, admin) reference the shared
  theme classes rather than duplicating modal/error/hint styling per screen
- A user-facing toggle (`ctrl+t`, a global priority binding so it works even while a modal's
  input field has focus) switches between dark and light mode; the home screen subtitle
  shows the current mode and updates live
- Layout and spacing on existing screens are revisited for visual hierarchy and consistency
  under the new theme (notably: error labels on report screens now render consistently with
  modal error labels), without changing underlying screen workflows or navigation
- The top-level navigation menus (home, reports, admin) render as a centered, rounded,
  bordered panel with a title and navigation hint, instead of a bare `ListView` stretched
  across the full terminal
- Historical report deltas (net worth history, account balance history) render in a
  contrasting color by direction — the active theme's success color for positive, error
  color for negative — via a shared `delta_text()` helper instead of plain `+`/`-` text
- `ruff`, `mypy`, and `pytest` pass (393 tests)

### [ ] Phase 40: HTML Graphical Reports

Goal:
Add the ability to export the net worth history report and the new single-account balance
history report (Phase 38) as self-contained HTML files with embedded charts, triggered from
both the CLI and the TUI.

Background:
Current reporting output is limited to terminal tables (Rich/Textual) and CSV. Some
reporting needs — sharing a trend visually, reviewing net worth trajectory graphically —
are better served by a chart than a table. Per the local-first, dependency-light standard
in `specs/tech-stack.md`, generated HTML files must be self-contained: viewable offline in
a browser with no network calls, using an embedded minimal charting library rather than a
CDN dependency.

Expected outcomes:

- A new export use case renders the net worth history report as a single self-contained
  HTML file with an embedded line chart (net worth, assets, and liabilities over time),
  with no external network dependency required to view it
- The same export path supports the single-account balance history report (Phase 38) as a
  line chart of balance over time
- A new CLI command (e.g. `nwtrack reports export-html`) accepts a report selection and
  target file path, mirroring the existing CSV export command pattern
- A TUI action on the relevant report screens triggers the same export use case and reports
  the output file path to the user
- Output-format and file-path handling preserve current default behavior for existing
  report commands; HTML export is strictly additive
- `ruff`, `mypy`, and `pytest` pass

### [ ] Phase 41: macOS Packaging And Deployment

Goal:
Package `nwtrack` for local installation on macOS via a `uv`-based install path, with
configuration and data files relocated to standard macOS application-support locations.

Background:
`nwtrack` currently runs from a source checkout via `uv run` with `.env`-based
configuration and a working-directory-relative database path. A packaged macOS install
should let a user install and run both the CLI and TUI entry points without manually
managing a source checkout, while keeping the install mechanism Python/`uv`-native rather
than introducing a compiled-binary toolchain. Code signing and notarization are explicitly
out of scope for this phase.

Expected outcomes:

- An install path (e.g. `uv tool install`) installs `nwtrack` such that both the CLI
  (`nwtrack ...`) and TUI (`nwtrack tui launch`) entry points are available on `PATH`
- Default configuration resolves to standard macOS locations when no `.env` is present:
  database under `~/Library/Application Support/nwtrack/`, logs under
  `~/Library/Logs/nwtrack/`
- Existing `.env`-based configuration continues to work unchanged for users who set it
  explicitly, preserving the current local-first configuration model
- First-run behavior creates required application-support and log directories
  automatically if missing
- Packaging and install steps are documented for a macOS user without requiring a source
  checkout beyond the documented install command
- Code signing and notarization are explicitly out of scope for this phase; unsigned
  Gatekeeper behavior is documented
- `ruff`, `mypy`, and `pytest` pass

## Planning Rules

- Keep phases small enough to land independently.
- Prefer schema-first changes before broad CLI rewiring.
- Preserve existing command behavior where practical until replacement paths are proven.
- Route new reporting work through shared aggregation primitives instead of adding more bespoke report logic.
- Prefer accounting-correct single-currency output; when conversion support is not available, fail clearly instead of summing mixed currencies.
- Treat testing and quality checks as part of phase validation, and document them explicitly in each phase spec.
- Update this roadmap when feature specs materially change implementation order.
