# nwtrack Tech Stack

## Purpose

This document defines the default implementation choices for `nwtrack` and the engineering constraints that new work should respect unless a spec explicitly changes them.

## Product Runtime

- Language: Python 3.12+
- Package and environment management: `uv`
- CLI framework: Typer
- Terminal rendering: Rich
- Database: SQLite
- ORM and persistence layer: SQLAlchemy 2.x
- Test framework: Pytest
- Linting and formatting: Ruff
- Static type checking: mypy

## Storage Model

- Primary datastore: local SQLite database
- Portability format: CSV
- Time granularity: monthly snapshots only, identified by `YYYY-MM`
- Money representation: integer smallest-unit amounts
- Exchange-rate handling: manual and local for now

## Domain Model Defaults

The default data model should continue to center on accounts and monthly balances, with explicit support for controlled reference data.

- `Category` remains a first-class entity and defines account side semantics.
- `Institution` is a first-class entity with its own CRUD workflows.
- `Tag` is a first-class entity with its own CRUD workflows.
- `Account` belongs to one category.
- `Account` may initially belong to zero or one institution, but the roadmap should move the product toward institution-required accounts.
- `Account` may reference zero, one, or many tags through an explicit association.
- Reporting should aggregate balances by account attributes such as category, side, institution, currency, and tag.
- Existing report commands should be preserved where practical as compatibility-oriented CLI surfaces over the same underlying reporting model.

## Architecture

The codebase follows a layered, ports-and-adapters style:

- `domain/`: core concepts and value objects
- `application/`: use cases, DTOs, ports, and services
- `bootstrap/`: composition and dependency injection
- `infra/`: SQLite, SQLAlchemy, configuration, persistence, and file I/O
- `entrypoints/cli/`: Typer commands, presenters, prompts, and terminal UI

Default architectural expectations:

- Domain rules stay independent from CLI concerns.
- Use cases coordinate workflows and return explicit outcomes.
- Infrastructure details stay behind ports where practical.
- Interactive behavior should move through presenter-style boundaries instead of mixing business logic with console I/O.
- Shared reporting logic should live below the CLI layer so compatibility commands and new aggregation commands use the same query and presentation primitives.

## Current Platform Decisions

These are intentional product constraints, not open-ended abstractions:

- SQLite is the product database for the foreseeable future.
- CSV import/export is sufficient for now.
- The product is CLI-first today.
- Reporting scope is CLI commands only.
- Future interface expansion should target a TUI before any other interface.
- Monthly snapshots are the permanent core model.

## Reporting Model

Reporting should follow one generalized balance-aggregation model instead of separate bespoke implementations.

- Aggregation dimension means the account attribute used to group balances, such as category, side, institution, currency, or tag.
- Single-month aggregation is a first-class use case.
- History aggregation across a start and end `YYYY-MM` range is a first-class use case.
- Aggregation dimensions should be explicit account attributes rather than report-specific query paths.
- Net worth reporting is the aggregation-by-side view of the same underlying model.
- Category reporting should converge on the same aggregation model while preserving user-facing compatibility where practical.
- Existing report commands should be treated as compatibility reporting surfaces over the shared aggregation model.

## Exchange Rates

Current default:

- Exchange rates are entered or loaded manually from local data.
- No network dependency is required for normal product use.

Future direction:

- Public-source fetching may be considered later.
- If added, fetched data must remain optional and must not weaken the local-first default.

## Engineering Standards

Every feature should begin with a spec.

Required quality gates before merge:

- Automated tests added or updated for the change
- `ruff` passes
- `mypy` passes
- `pytest` passes

Additional implementation standards:

- Prefer clear domain modeling over clever abstractions.
- Model controlled reference data explicitly instead of encoding it as unchecked free text when the product requires reuse or validation.
- Avoid raw SQL unless there is a justified performance or expressiveness need.
- If raw SQL is introduced, the spec or change should explain why SQLAlchemy ORM/query APIs were insufficient.
- Favor compatibility-preserving CLI changes unless a spec explicitly calls for a breaking change.
- Keep local workflows fast and dependency-light.
- Each phase spec must define its own validation steps, including feature-specific testing expectations and required quality checks.
- Validation for a phase is incomplete if it only references generic repository commands without stating what the feature must prove.

## Development Workflow

The default workflow for new work is:

1. Write or update a spec in `specs/`.
2. Define phase validation, including feature-specific tests, manual checks, and quality gates.
3. Confirm domain rules and user-facing behavior.
4. Implement the smallest viable slice.
5. Add or update tests.
6. Run lint, type checks, and tests.
7. Update the constitution or feature spec if the design changed during implementation.

## Documentation Rules

- Long-lived direction belongs in the constitution documents.
- Feature-specific behavior belongs in feature specs under `specs/`.
- Feature specs should describe validation in enough detail that phase completion can be checked from the spec itself.
- README content should stay user-oriented.
- Legacy notes in [stakeholder-input.md](/Users/48678/ext-repos/nwtrack/specs/stakeholder-input.md) are superseded by this constitution.
