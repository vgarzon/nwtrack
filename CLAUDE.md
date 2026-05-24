# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

nwtrack is a personal net worth tracking application with a CLI interface. Data is stored in a local SQLite database, and the application allows users to track assets and liabilities across different accounts, categories, and currencies over time.

## Architecture

This project follows a clean architecture pattern with clear separation of concerns:

### Layer Structure

```
src/nwtrack/
├── domain/           # Core business entities and value objects
├── application/      # Business logic layer
│   ├── ports/        # Interface protocols (Repository, UnitOfWork, etc.)
│   ├── registries/   # Dynamic registration of mappers and repositories
│   ├── services/     # Application services
│   └── use_cases/    # Entry points for business operations
├── bootstrap/        # Dependency injection and composition
├── infra/            # Infrastructure implementations
│   ├── config/       # Settings and configuration
│   ├── fileio/       # CSV file operations
│   ├── persistence/  # Database-agnostic ORM layer
│   │   ├── orm/      # ORM models (base, types, entity mappings)
│   │   ├── repositories/  # SQLAlchemy repository implementations
│   │   ├── uow.py    # Unit of Work implementation
│   │   └── schema.py # Schema manager
│   └── db/           # Database dialect-specific implementations
│       └── sqlite/   # SQLite session manager with PRAGMAs
└── entrypoints/      # External interfaces
    └── cli/          # Typer-based CLI application
```

### Key Architectural Patterns

**Domain Layer**: Domain models are simple dataclasses (Currency, Category, Account, Balance, ExchangeRate, NetWorth). The `Month` value object provides month-based date handling with validation.

**Application Layer**:
- **Ports**: Python Protocols defining interfaces for repositories, mappers, presenters, and the Unit of Work pattern
- **Registries**: `MapperRegistry` and `RepositoryRegistry` enable dynamic registration of domain types to their infrastructure implementations
- **Services**: Application services provide cross-cutting concerns:
  - `FetchService`: Read-only data retrieval operations (no side effects)
  - `InitDataService`: Database initialization with CSV data
  - `DBAdminService`: Database administration operations
  - `ExportCSVService`: CSV export operations
- **Use Cases**: Each use case is a class-based module with:
  - Constructor dependency injection (UoW, services, presenters)
  - A `run()` method that returns `OperationResult[T]`
  - A `main()` function for standalone execution and CLI integration

**Presentation Layer** (Ports & Adapters Pattern):
- **Presentation Ports** (`application/ports/presentation.py`): Protocol interfaces defining UI contracts
  - Examples: `AccountCreationPresenter`, `BalanceUpdatePresenter`, `NetworthHistoryPresenter`
  - Define methods for displaying data, collecting input, showing messages
- **Presentation Adapters** (`entrypoints/cli/adapters/`): Rich-based concrete implementations
  - Examples: `RichAccountCreationPresenter`, `RichBalanceUpdatePresenter`
  - Handle all console UI interactions (tables, prompts, formatting)
  - Injected into use cases via DI, enabling clean separation and testability
- **Migration Status**: Presenter pattern is applied to all interactive use cases — migration is complete. No use case module imports Rich directly.

**Infrastructure Layer**:
- **Persistence Layer** (`infra/persistence/`) - Database-agnostic ORM components:
  - ORM models split into focused modules: `base.py` (Declarative Base), `types.py` (custom TypeDecorators), `models.py` (entity mappings)
  - Uses SQLAlchemy 2.0 ORM with declarative mapping via `MappedAsDataclass`
  - Repositories (`repositories/`) implement protocol interfaces using SQLAlchemy Session
  - `SQLAlchemyUnitOfWork` implements UoW pattern, wrapping SQLAlchemy Session
  - Repositories instantiated on UoW entry and share the same session for atomic transactions
  - Custom `MonthType` TypeDecorator handles Month value object persistence
  - Entity IDs use `init=False` for auto-increment primary keys
- **Database Dialect Layer** (`infra/db/`):
  - SQLite-specific session manager with PRAGMA commands and connection settings
  - `SQLiteSessionManager` creates engine and session factory with SQLite-specific configuration
- All database queries use SQLAlchemy ORM exclusively (no raw SQL)
- `SchemaManager` implementation abstracts schema operations (create/drop tables) from application layer

**Dependency Injection**: A custom lightweight DI container (`bootstrap/container.py`) supports singleton and transient lifetimes. Each use case's `main()` function extends the base container from `bootstrap/composition.py` with its specific dependencies.

**CLI Layer**: Uses Typer with sub-apps for different command groups (accounts, balances, categories, reports, export). Commands are thin wrappers that import and invoke use case `main()` functions.

### Important Design Decisions

1. **Amounts as Integers**: All balance amounts are stored as integers (e.g., cents for USD). Liabilities are stored as positive amounts; their "side" (asset/liability) is tracked via the category relationship.

2. **Month Value Object**: Dates are represented as `Month(year, month)` throughout the application, stored in database as 'YYYY-MM' strings.

3. **Callable UoW Pattern**: Use cases and services receive `uow: Callable[[], UnitOfWork]` (factory function) to create new UoW instances per operation, enabling proper transaction boundaries. This allows each operation to have its own transaction context.

4. **Lazy Use Case Imports**: CLI commands use lazy imports (`import nwtrack.application.use_cases.foo as foo`) to improve startup time.

5. **Presentation Layer Separation**: Interactive use cases depend on presenter Protocol interfaces rather than concrete UI implementations, enabling clean separation between business logic and presentation concerns. Presenters handle all user interaction (prompts, displays, messages).

6. **Operation Result Pattern**: Use cases return `OperationResult[T]` containing success status and optional data, providing a consistent interface for handling outcomes and errors.

7. **SQLAlchemy ORM Integration**: Domain entities use SQLAlchemy's `MappedAsDataclass` for ORM mapping while preserving dataclass behavior:
   - Entities remain pure dataclasses with SQLAlchemy annotations
   - Auto-increment ID fields use `init=False` and are set after insert
   - Repository `hydrate()` methods skip `id=0` (sentinel for auto-generation)
   - Custom `MonthType` TypeDecorator converts between Month objects and string storage
   - Session configured with `expire_on_commit=False` to allow entity usage after commit
   - CSV export uses SQLAlchemy's mapper inspection to get correct database column names
   - ORM relationships use `viewonly=True` + `lazy="selectin"` + `init=False, default=None, compare=False, repr=False`: `Account.category` and `Balance.account` are loaded in a batched SELECT before session closes, making `balance.account.category` accessible after the UoW context exits. `viewonly=True` is critical — omitting it causes SQLAlchemy to null out the FK column when the relationship field is `None` at construction time.

8. **Schema Management Port**: Schema operations (create/drop tables) are abstracted via `SchemaManager` protocol, with SQLAlchemy implementation in infrastructure. Follows ports-and-adapters pattern keeping application layer independent of SQLAlchemy engine details.

## Development Commands

The project includes a `justfile` for running common commands. Install `just` if you don't have it: https://github.com/casey/just

```bash
# List all available commands
just

# Run all checks (lint + typecheck + test)
just check
```

### Environment Setup

The project uses `uv` for dependency management and requires Python 3.12+.

```bash
# Install dependencies
uv sync
# OR
just install

# Activate virtual environment
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows
```

### Common Just Commands

```bash
# Testing
just test              # Run all tests
just test-v            # Run tests with verbose output
just test-file <path>  # Run specific test file
just test-pattern <pattern>  # Run tests matching pattern

# Code quality
just lint              # Run ruff linter
just lint-fix          # Auto-fix linting issues
just format            # Format code with ruff
just typecheck         # Run mypy type checker
just check             # Run all checks (lint + typecheck + test)

# CLI commands
just cli-help          # Show CLI help
just accounts-list     # List accounts
just balances-update   # Update balances interactively
just report-networth   # Show networth report

# Maintenance
just clean             # Remove Python cache files
```

### Git Workflow

- Treat `devel` as the default integration branch.
- Create new feature branches from `devel`.
- Open feature pull requests against `devel`.
- Promote `devel` to `main` through separate pull requests after changes are validated.
- Do not merge routine feature work directly into `main`.

### Running the Application

```bash
# Run CLI using uv
uv run nwtrack --help

# Common commands
uv run nwtrack accounts list
uv run nwtrack accounts create
uv run nwtrack balances update
uv run nwtrack reports networth
uv run nwtrack export csv

# Or use just targets (recommended for common operations)
just accounts-list
just balances-update
just report-networth
```

### Testing

```bash
# Run all tests
uv run pytest
# Or use just
just test

# Run specific test file
uv run pytest tests/use_cases/test_list_accounts.py
# Or use just
just test-file tests/use_cases/test_list_accounts.py

# Run tests with verbose output
uv run pytest -v
# Or use just
just test-v

# Run tests matching a pattern
uv run pytest -k "test_account"
# Or use just
just test-pattern "test_account"
```

**Test Structure**: Tests mirror the source structure. The `conftest.py` provides fixtures for:
- `base_container`: DI container with SQLAlchemy-based UoW and temporary file database
- `sample_entities`: Preloaded test data from CSV files in `tests/data/csv/`
- `base_config`: Settings configured for temporary file database (enables SQLAlchemy + DBConnectionManager sharing)
- Note: Tests use temp files instead of `:memory:` to allow both SQLAlchemy and legacy DBConnectionManager to access the same database

### Linting and Type Checking

```bash
# Linting with ruff
uv run ruff check src/ tests/
# Or use just
just lint

# Auto-fix linting issues
uv run ruff check --fix src/ tests/
# Or use just
just lint-fix

# Format code with ruff
uv run ruff format src/ tests/
# Or use just
just format

# Type checking with mypy
uv run mypy src/ tests/
# Or use just
just typecheck

# Run all checks (lint + typecheck + test)
just check

# Note: Project uses mypy with path configured to src/
```

### Database Operations

The database schema is managed entirely through SQLAlchemy ORM models in `src/nwtrack/infra/persistence/orm/models.py`. Schema creation is handled by `Base.metadata.create_all()` via the `SchemaManager` implementation.

The application uses:
- SQLite database (default: `data/sqlite/nwtrack.db`)
- Tables: currencies, categories, accounts, balances, exchange_rates
- ORM models with CHECK constraints (Category.side, Account.status) and composite UNIQUE constraints (Balance, ExchangeRate)
- NetWorth aggregations computed via SQLAlchemy queries (replaces previous networth_history view)

Environment variables are loaded from `.env` (see `.env_example` for template):
- `NWTRACK_DB_FILE_PATH`: Database file location (default: `data/sqlite/nwtrack.db`)
- `NWTRACK_LOG_FILE`: Log file location (default: `./logs/nwtrack.log`)
- `NWTRACK_LOG_FILE_LEVEL`: Logging level (default: `INFO`)
- `NWTRACK_LOG_ROTATION_MB`: Log file rotation size in MB (default: `10`)
- `NWTRACK_LOG_BACKUP_COUNT`: Number of backup log files to keep (default: `7`)

**Note**: File logging is enabled by default. The application automatically creates the log directory if it doesn't exist and uses rotating file handlers to prevent unbounded log growth.

## Code Conventions

**Data Flow**: CSV → dict records → domain entities (via `hydrate()`) → database (via SQLAlchemy ORM)

**Repository Methods**: Follow naming conventions:
- `get()` / `get_by_id()` / `get_by_name()`: Retrieve single entity (returns None if not found)
- `get_all()` / `get_active()`: Retrieve multiple entities
- `get_dict()` / `get_dict_id()`: Return dict indexed by key
- `insert()` / `insert_many()`: Insert entities (uses `session.add()`, `session.flush()` to get ID)
- `update()` / `update_*()`: Update operations (uses `session.merge()` for detached entities)
- `delete_by_id()` / `delete_all()`: Delete operations (uses SQLAlchemy `delete()` construct)
- `hydrate()` / `hydrate_many()`: Convert dicts to entities (skips id=0 for auto-generation)

**SQLAlchemy Repository Patterns**:
```python
# Query pattern
def get_by_id(self, entity_id: int) -> Entity | None:
    return self._session.execute(
        select(Entity).where(Entity.id == entity_id)
    ).scalar_one_or_none()

# Insert pattern
def insert(self, entity: Entity) -> int:
    self._session.add(entity)
    self._session.flush()  # Get ID without committing
    return entity.id

# Hydrate pattern (for entities with auto-increment IDs)
def hydrate(self, record: dict) -> Entity:
    entity = Entity(name=record["name"], ...)
    # Only set id if present and non-zero (0 = auto-generate)
    if "id" in record and int(record["id"]) > 0:
        entity.id = int(record["id"])
    return entity
```

**Use Case Pattern**: Each use case module follows this structure:
1. **Class Definition**: A class that encapsulates the business logic (e.g., `AccountCreator`, `BalanceUpdater`)
2. **Constructor Injection**: Receives dependencies via `__init__` (UoW factory, services, presenter protocols)
3. **Run Method**: A `run()` method that orchestrates the workflow and returns `OperationResult[T]`
4. **Main Function**: A `main()` function that:
   - Builds and configures the DI container
   - Resolves dependencies
   - Instantiates and executes the use case
   - Returns the operation result
5. **Standalone Execution**: Can be run directly: `uv run python -m nwtrack.application.use_cases.update_balances`

**Typical Use Case Flow**:
```python
class MyUseCase:
    def __init__(self, uow: Callable[[], UnitOfWork],
                 fetcher: FetchService, presenter: MyPresenter) -> None:
        self._uow = uow
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self) -> OperationResult[ResultType]:
        # 1. Present UI
        self._presenter.show_header()

        # 2. Fetch data
        data = self._fetcher.get_something()

        # 3. Collect input via presenter
        user_input = self._presenter.prompt_for_input()

        # 4. Execute business logic with transaction
        with self._uow() as uow:
            entity = uow.repository.update(user_input)

        # 5. Show result
        self._presenter.show_success()
        return OperationResult(success=True, data=entity.id)
```

**Testing Pattern**: Use pytest fixtures for container setup and sample data. Tests use `:memory:` SQLite databases for fast execution. UoW factory pattern: `lambda: container.resolve(UnitOfWork)` creates new UoW instances per test operation.

**Dependency Flow**: The application follows strict dependency direction:
- **CLI Commands** → **Use Cases** → **Services/Repositories** → **Database**
- **Presentation**: Use Cases depend on Presenter Protocols (interfaces), not concrete implementations
- **Persistence**: Use Cases depend on UnitOfWork Protocol, not SQLAlchemy specifics
- **ORM Layer**: Repositories depend on SQLAlchemy Session, not exposed to use cases
- **Data Fetching**: Use Cases use FetchService for read operations to avoid mixing reads with transactional writes

**Refactoring Guidelines**:
- When refactoring use cases to use the presentation layer:
  1. Define a presenter Protocol in `application/ports/presentation.py`
  2. Create a Rich adapter in `entrypoints/cli/adapters/`
  3. Update use case to accept presenter via constructor
  4. Move all console/UI interactions to presenter methods
  5. Update `main()` function to register presenter in DI container
  6. Update CLI command if needed
  7. Update tests to use mock presenters
