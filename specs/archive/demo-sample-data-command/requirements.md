# Requirements: Demo Sample Data Command

## Problem

There is no way to get a populated nwtrack database without entering real data or hand-building
CSVs. Demos, screenshots, manual testing, and first-time users all need a small, realistic
database that is safe to explore.

## Scope

### Included

- New CLI command `nwtrack admin create-sample-db PATH`.
- `PATH` is a **required** positional argument: the SQLite file to create.
- The command creates a brand-new database at `PATH` with the current schema (via
  `SchemaManager.create_all_tables()`, which stamps at Alembic `head`) and fills it with a
  minimal representative dataset generated in code.
- After success the command tells the user how to activate the database (see Output).

### Sample dataset

Minimal and representative, not comprehensive over the schema.

| Entity | Content |
|---|---|
| Currencies | 2 (USD, CHF) |
| Exchange rates | CHF series covering the balance months |
| Categories | A few asset and liability categories (e.g. checking, savings, investment, mortgage, revolving_credit) |
| Institutions | 2-3 fictional institutions |
| Tags | 2-3 (e.g. core, long-term) |
| Accounts | ~6-8 across asset/liability categories, both currencies, all with an institution; at least one tagged; at least one inactive |
| Account status history | Consistent with account status and balance months |
| Balances | 12 months ending at the current month, plausible month-over-month movement, liabilities stored as positive amounts per existing convention |

Names, institutions, and amounts are obviously fictional.

### Not included

- No overwrite or `--force` option.
- No `--config-file` rewriting: the command never edits `config.toml`.
- No randomised or user-tunable dataset size, locale, or currency choice.
- No changes to the schema (no Alembic revision).
- No TUI surface.

## Decisions

1. **Refuse if the target exists.** If `PATH` exists (file, directory, or symlink), exit
   non-zero with a clear error and touch nothing. This is the guard that protects production
   data: the real database can never be overwritten because any existing path is rejected.
   No `--force` flag, by design.
2. **Never touch the active database.** The Typer root callback currently runs
   `_ensure_runtime_schema()` for every command except `config`, which would create or migrate
   the user's configured database as a side effect. `admin create-sample-db` must be exempt
   from that startup step, like `config` commands.
3. **Data built in code, through the application layer.** A new use case (`CreateSampleDatabase`)
   builds domain entities and inserts them via UoW/repositories against an engine pointed at
   `PATH`. No raw SQL, no bundled CSV package data, no new dependencies.
4. **Month-relative data.** Balances end at the current month so the TUI startup balance check
   and reports show fresh data rather than a stale demo.
5. **Failure cleanup.** If creation fails after the file was created, remove the partial file
   (only a file this command created) and report the error.
6. **Parent directory.** If the parent directory of `PATH` does not exist, fail with a clear
   error rather than creating directories.

## Output

On success, via a Rich presenter, the command prints:

- The absolute path of the created database and a short summary of what it contains (counts of
  accounts, balances, etc.).
- How to activate it, in both forms:
  - `config.toml`: `[database]` with `db_file_path = "<absolute path>"` (mention
    `nwtrack config show` to find the active config file, and `nwtrack config init` if none exists).
  - One-off alternative: `NWTRACK_DATABASE__DB_FILE_PATH=<path>`.
- A note that the command did not change any configuration and that the current database is untouched.

## Context

- Follow the use-case pattern in `CLAUDE.md`: class with constructor injection, `run()` returning
  `OperationResult[T]`, `main()` building the container; lazy import in the Typer command.
- Add a presenter Protocol in `application/ports/presentation.py` and a Rich adapter under
  `entrypoints/cli/adapters/` (no Rich in the use case).
- Place the command in `entrypoints/cli/commands/admin.py` next to the existing admin commands.
- Because the root callback ignores the command, the use case must not load or open the
  configured database; the target engine is built from `PATH` only (a `Settings` with
  `db_file_path=PATH`, or equivalent).
- Update `README.md` (new-user section), `CLAUDE.md` CLI command list, and `CHANGELOG.md`.
- Tone: concise, same style as the other admin presenters.
