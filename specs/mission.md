# nwtrack Mission

## Purpose

`nwtrack` is a single-user monthly balance tracking tool and learning project.

Its job is to make monthly financial tracking fast, reliable, and local-first:

1. Low-friction monthly updates
2. Strong CLI ergonomics
3. Local ownership of data
4. Accounting correctness

The product should help one person maintain a clean month-by-month view of assets and liabilities without introducing the overhead of full transaction tracking.

## Product Shape

`nwtrack` is CLI-first today.

The near-term product is a local command-line application with interactive workflows and readable terminal output. The longer-term direction is a terminal user interface (TUI), not a web app or hosted service.

Monthly snapshots are the permanent core model of the product. `nwtrack` is not a transaction ledger, budgeting tool, or brokerage sync product.

Accounts are the central record shape. Over time, accounts should support richer classification and reporting through category, side, institution, currency, and controlled tags.

## Intended User

- A single user
- Working locally on their own machine
- Comfortable using the terminal
- Willing to manage their own data files and database
- Using the project both as a practical tool and as a software design learning exercise

## Core Principles

### Low-Friction Updates

Entering and maintaining monthly balances should be the shortest path through the product. Common monthly workflows should be faster and clearer than one-off administration tasks.

### CLI Ergonomics First

Commands, prompts, defaults, and output should feel intentional. Interactive flows should minimize re-entry, reduce ambiguity, and make the common path obvious.

### Local Ownership

User data lives locally in SQLite and portable CSV files. The user should be able to inspect, export, back up, and recover their data without relying on a remote service.

### Accounting Correctness

Balances, account classification, exchange-rate handling, transfer logic, and historical reporting must remain internally consistent. Convenience features must not weaken correctness.

### Reporting By Composition

Reporting should come from composable aggregation over account attributes instead of one-off report types. Net worth reporting is one important view, not a separate data model.

### Simple by Design

The monthly snapshot model is a feature, not a temporary shortcut. New work should preserve that simplicity unless there is a compelling product reason to change it.

## Product Boundaries

### In Scope

- Tracking assets and liabilities by month
- Managing accounts, categories, institutions, tags, balances, and exchange rates
- Reporting balances for a single month or across month history by account attributes
- Preserving compatibility with existing CLI reporting where practical
- CSV-based import/export for portability, backup, and recovery
- Local-only operation by default
- Incremental evolution from CLI toward TUI

### Out of Scope for Now

- Multi-user support
- Cloud sync
- Bank or brokerage integrations
- Automatic exchange-rate fetching
- Transaction-level accounting
- Budgeting and forecasting
- Multiple database backends

## Spec-Driven Development Constitution

Every meaningful feature starts with a written spec before implementation.

Shared terminology for specs and implementation phases:

- Institution: the financial institution where an account is held.
- Tag: a reusable account label used for grouping and reporting.
- Aggregation dimension: the account attribute used to group balances, such as category, side, institution, currency, or tag.
- Single-month aggregation: grouped balances for one `YYYY-MM` month.
- History aggregation: grouped balances across a start and end `YYYY-MM` range.
- Compatibility reporting: existing user-facing report commands that should converge on the shared aggregation model where practical.

The spec should define:

- User problem
- Scope and non-goals
- Data and domain impact
- CLI or TUI behavior
- Validation and error cases
- Feature-specific testing and quality checks
- Acceptance criteria

Each phase-level spec must treat validation as concrete work, not a placeholder section.

Validation should explicitly define:

- The automated tests or test updates required for the phase
- The manual validation steps required for the phase
- The quality checks that must pass for the phase, such as linting, type checking, and related gates
- Any important error cases, compatibility checks, or regression risks that need verification

Code should follow the spec. If implementation pressure reveals a better direction, the spec should be updated first or alongside the change, not after the fact.

## Governance

This constitution is a living document.

Rules for maintaining it:

1. `specs/mission.md` defines long-lived product intent and decision priorities.
2. `specs/tech-stack.md` defines the default implementation constraints and engineering standards.
3. `specs/roadmap.md` defines the current best known implementation order in small phases.
4. Feature specs should be added under `specs/` as the project evolves.
5. When product direction changes, update the constitution in the same change set as the code or feature spec that triggered the change.
6. The constitution supersedes [stakeholder-input.md](/Users/48678/ext-repos/nwtrack/specs/stakeholder-input.md) as the source of truth for ongoing project direction.
