# justfile for nwtrack development commands

# List available commands
default:
    @just --list

# Install dependencies
install:
    uv sync

# Run all tests
test:
    uv run pytest tests/

# Run tests with verbose output
test-v:
    uv run pytest -v tests/

# Run specific test file
test-file FILE:
    uv run pytest {{FILE}}

# Run tests matching a pattern
test-pattern PATTERN:
    uv run pytest -k {{PATTERN}}

# Run linter
lint:
    uv run ruff check .

# Auto-fix linting issues
lint-fix:
    uv run ruff check --fix .

# Format code
format:
    uv run ruff format .

# Type check with mypy
typecheck:
    uv run mypy .

# Run all checks (lint + typecheck + test)
check: lint typecheck test

# Run CLI help
cli-help:
    uv run nwtrack --help

# List accounts
accounts-list:
    uv run nwtrack accounts list

# Create account interactively
accounts-create:
    uv run nwtrack accounts create

# Update balances interactively
balances-update:
    uv run nwtrack balances update

# Delete balance interactively
balances-delete:
    uv run nwtrack balances delete

# Show networth report
report-networth:
    uv run nwtrack reports networth

# Export data to CSV
export-csv:
    uv run nwtrack export csv

# Clean up Python cache files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
