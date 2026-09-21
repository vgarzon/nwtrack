# nwtrack

A personal net worth tracking application with a CLI and TUI interface.

## Features

- Track assets and liabilities across multiple accounts, categories, currencies, institutions, and tags
- Record account balances over time (month-based tracking)
- Account status history: track when accounts became active, inactive, or closed
- Support for exchange rates between currencies
- Generate net worth reports with historical trends and month-over-month deltas
- Aggregated balance reports by category, side, institution, currency, or tag — single-month or history range
- Interactive TUI built with Textual (launched via `nwtrack tui launch`)
- Interactive CLI built with Typer and Rich
- Export and import data via CSV for portability and backup

## Installation

Requires Python 3.12+ and [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install dependencies
uv sync

# Run the application
uv run nwtrack --help
```

## Configuration

nwtrack reads settings from `config.toml`, searched in this order (first found wins):

1. `~/Library/Application Support/nwtrack/config.toml` (macOS) /
   `~/.local/share/nwtrack/config.toml` (Linux, via [`platformdirs`](https://github.com/tox-dev/platformdirs))
2. `~/.config/nwtrack/config.toml`
3. `./config/nwtrack/config.toml` (relative to the working directory — convenient for a
   source checkout)

Run `nwtrack config init` to write a default `config.toml` (with platform-appropriate
default database and log paths already filled in) to the first location above. See
[`config.example.toml`](./config.example.toml) for the full format.

If no `config.toml` is found, nwtrack falls back to built-in defaults and prints/logs the
paths it searched.

Every setting can be overridden with a shell environment variable of the same name, using
`NWTRACK_<SECTION>__<KEY>` (double underscore), e.g. `NWTRACK_DATABASE__DB_FILE_PATH` or
`NWTRACK_LOGGING__LOG_FILE_LEVEL`. Relative paths in `config.toml` (e.g.
`"./data/sqlite/nwtrack.db"`) resolve against the current working directory at process
start, not against the config file's own location — this is what lets a source checkout use
a `./config/nwtrack/config.toml` with repo-relative paths.

## Usage

```bash
# Launch the TUI
uv run nwtrack tui launch
```

The TUI is the primary interface. It covers all balance workflows, reporting, account management, and administrative CRUD for categories, institutions, and tags.

### CLI (administrative tasks)

The CLI remains available for scripting, one-off administration, and CSV data management:

```bash
# CSV export and import
uv run nwtrack export csv
uv run nwtrack import tables-csv

# Admin
uv run nwtrack admin seed-status-history

# Reports (non-interactive)
uv run nwtrack reports networth-history
uv run nwtrack reports balances-aggregate
uv run nwtrack reports balances-aggregate-history
uv run nwtrack reports account-history --account-name <name> --start YYYY-MM --end YYYY-MM

# Account and reference-data administration
uv run nwtrack accounts list
uv run nwtrack institutions list
uv run nwtrack tags list
```

## Architecture

Built with clean architecture principles:
- **Domain Layer**: Core entities (Account, Balance, Currency, Institution, Tag, ExchangeRate, etc.)
- **Application Layer**: Use cases and business logic with dependency injection; presenter Protocol interfaces for all interactive flows
- **Infrastructure Layer**:
  - Database-agnostic ORM layer using SQLAlchemy 2.0
  - SQLite dialect-specific session management
  - Repository pattern with Unit of Work for transaction management
- **Entrypoints**:
  - Textual-based TUI with a home screen, screen-stack navigation, and screens for all primary workflows
  - Typer-based CLI with Rich UI components and presenter adapters (administrative and scripting surface)

Data is stored in a local SQLite database. Tables: currencies, categories, institutions, tags, accounts, account\_status\_history, balances, exchange\_rates.

## Quick start

```bash
# Install just if needed: https://github.com/casey/just
just install        # Install dependencies
just check          # Run linting, type checking, and tests
just test           # Run tests
```

## Development Workflow

- Create feature branches from `devel`.
- Open and merge feature pull requests into `devel`.
- Promote validated changes from `devel` to `main` with separate pull requests.
- Do not target feature pull requests directly at `main`.
