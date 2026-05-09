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

### [ ] Phase 13: Tag Schema Foundation

Goal:
Add controlled tags and account-to-tag associations in the data model.

Expected outcomes:

- `Tag` entity, ORM mapping, association table, repository support, and tests exist
- Accounts can reference zero, one, or many tags by ID
- Database migration path preserves existing account and balance records
- CSV import/export behavior is updated or explicitly deferred in the feature spec

### [ ] Phase 14: Tag CLI CRUD

Goal:
Make tags independently manageable before wiring them into account workflows.

Expected outcomes:

- CLI commands exist to create, list, update, and delete tags
- Validation preserves controlled-label behavior
- Deletion and rename semantics are defined and tested

### [ ] Phase 15: Account Workflows With Tags

Goal:
Thread tag assignment through account management in a way that remains efficient for monthly workflows.

Expected outcomes:

- Account create/update commands can attach and detach tags
- Account listing and selection flows can surface tags where useful
- Account fetch/read models expose tags for reporting and presentation
- Tests cover empty, single-tag, and multi-tag account cases

### [ ] Phase 16: Shared Aggregation Query Layer

Goal:
Build one reporting core for balance aggregation by account attributes.

Expected outcomes:

- Shared query/use-case support exists for aggregation by category, side, institution, currency, and tag
- Single-month aggregation is implemented first
- Tag aggregation semantics for multi-tag accounts are explicitly defined in the feature spec and tests
- Report outputs remain CLI-oriented

### [ ] Phase 17: New Single-Month Aggregated Balance Report

Goal:
Expose the generalized single-month report through a dedicated CLI command.

Expected outcomes:

- A CLI report command accepts a month and one aggregation dimension
- Rich output presents grouped balances clearly
- Existing net worth and category reporting commands continue to work during this phase

### [ ] Phase 18: History Aggregated Balance Report

Goal:
Extend the shared aggregation model to month history between two `YYYY-MM` values.

Expected outcomes:

- A CLI report command accepts start month, end month, and one aggregation dimension
- Output shows per-month grouped balances over the requested range
- History reporting reuses the shared aggregation core rather than duplicating query logic

### [ ] Phase 19: Compatibility Convergence

Goal:
Move older reporting commands onto the generalized reporting core while preserving user-facing behavior where practical.

Expected outcomes:

- Existing net worth reporting uses aggregation-by-side internally
- Existing category balance reporting uses aggregation-by-category internally
- CLI output changes are limited to what is necessary for consistency or new data requirements
- Compatibility differences are documented in release notes or feature specs

### [ ] Phase 20: Institution Requirement Migration Plan

Goal:
Prepare the product to make institutions required on accounts in a later change without disrupting current users.

Expected outcomes:

- A migration strategy exists for accounts that still lack institutions
- CLI and validation rules can identify and remediate missing institutions
- The spec defines the cutover criteria for making institution assignment mandatory

## Planning Rules

- Keep phases small enough to land independently.
- Prefer schema-first changes before broad CLI rewiring.
- Preserve existing command behavior where practical until replacement paths are proven.
- Route new reporting work through shared aggregation primitives instead of adding more bespoke report logic.
- Treat testing and quality checks as part of phase validation, and document them explicitly in each phase spec.
- Update this roadmap when feature specs materially change implementation order.
