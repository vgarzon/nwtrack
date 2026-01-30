# nwtrack

A personal net worth tracking application with a CLI interface.

## Features

- Track assets and liabilities across multiple accounts, categories, and currencies
- Record account balances over time (month-based tracking)
- Support for exchange rates between currencies
- Generate net worth reports with historical trends
- Export data to CSV
- Interactive CLI built with Typer and Rich

## Installation

Requires Python 3.12+ and [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install dependencies
uv sync

# Run the application
uv run nwtrack --help
```

## Usage

```bash
# List accounts
uv run nwtrack accounts list

# Create a new account
uv run nwtrack accounts create

# Update balances interactively
uv run nwtrack balances update

# View net worth report
uv run nwtrack reports networth

# Export data to CSV
uv run nwtrack export csv
```

## Architecture

Built with clean architecture principles:
- **Domain Layer**: Core entities (Account, Balance, Currency, etc.)
- **Application Layer**: Use cases and business logic with dependency injection
- **Infrastructure Layer**: SQLite repositories and mappers
- **Entrypoints**: Typer-based CLI

Data is stored in a local SQLite database with tables for currencies, categories, accounts, balances, and exchange rates.

## Quick start:
```bash
# Install just if needed: https://github.com/casey/just
just install        # Install dependencies
just check          # Run linting, type checking, and tests
just test           # Run tests
```

