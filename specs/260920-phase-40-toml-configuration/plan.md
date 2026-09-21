# Phase 40: TOML-Based Configuration Management — Plan

## 1. Dependencies [x]

1.1. [x] Add `platformdirs` to `pyproject.toml` dependencies.
1.2. [x] Remove `python-dotenv` from `pyproject.toml` dependencies.
1.3. [x] `uv sync` / `uv lock` to update the lockfile.

## 2. Settings shape [x]

2.1. [x] Expand `infra/config/settings.py`'s `Settings` dataclass to carry all current
     configuration fields (still a plain frozen dataclass, no validation library):
     `db_file_path: str`, `log_file: str`, `log_file_level: str`, `log_rotation_mb: int`,
     `log_backup_count: int`.
2.2. [x] Keep `Settings` free of any TOML/env-parsing logic — it stays a pure data container,
     consistent with existing conventions.

## 3. Config path resolution [x]

3.1. [x] Add a small module (e.g. `infra/config/paths.py`) exposing:
     - `resolve_config_file() -> Path | None` — searches, in order:
       `platformdirs.user_config_dir("nwtrack")/config.toml`,
       `~/.config/nwtrack/config.toml`, `./config/nwtrack/config.toml`; returns the first
       path that exists, or `None` if none do.
     - `default_config_dir() -> Path` — `platformdirs.user_config_dir("nwtrack")`, used as
       the write target for `nwtrack config init`.
     - `default_db_file_path() -> Path` — `platformdirs.user_data_dir("nwtrack") / "nwtrack.db"`.
     - `default_log_file_path() -> Path` — `platformdirs.user_log_dir("nwtrack") / "nwtrack.log"`.
3.2. [x] Ensure parent directories are created (`Path.mkdir(parents=True, exist_ok=True)`) at
     the point a file is actually written (config init, db init, log setup) — not eagerly
     on import. **Implementation note**: also applied to `SQLiteSessionManager.__init__`
     (`infra/db/sqlite/manager.py`), since opening the SQLite engine is the point the DB
     file is actually created — this wasn't explicitly called out per-module in the plan but
     follows directly from the "point a file is actually written" principle. Without it, a
     fresh install with no `data/` directory yet would fail with
     `sqlite3.OperationalError: unable to open database file` the first time any command ran.
3.3. [x] A relative `db_file_path`/`log_file` string read from `config.toml` is resolved via
     `Path(value).resolve()` (relative to the process's current working directory) — never
     relative to `config.toml`'s own location. Absolute paths pass through unchanged. This
     resolution happens in `load.py` (section 4), not in `paths.py`, since it applies to
     user-supplied TOML values rather than the platformdirs-derived defaults.

## 4. Config file loading [x]

4.1. [x] Rewrite `infra/config/load.py`:
     - Remove `load_dotenv`/`find_dotenv` usage and the `python-dotenv` import.
     - Locate `config.toml` via `resolve_config_file()`. If found, parse with stdlib
       `tomllib` into a dict; if not found, log/print guidance (paths searched, how to run
       `nwtrack config init`) and proceed with in-code defaults only.
     - Read `[database].db_file_path` (default: `default_db_file_path()`) and
       `[logging].log_file` / `log_file_level` / `log_rotation_mb` / `log_backup_count`
       (defaults: `default_log_file_path()`, `"INFO"`, `10`, `7`).
     - Apply environment variable overrides, checked after the TOML value is resolved:
       `NWTRACK_DATABASE__DB_FILE_PATH`, `NWTRACK_LOGGING__LOG_FILE`,
       `NWTRACK_LOGGING__LOG_FILE_LEVEL`, `NWTRACK_LOGGING__LOG_ROTATION_MB`,
       `NWTRACK_LOGGING__LOG_BACKUP_COUNT`.
     - Raise a clear, actionable error for malformed TOML (invalid syntax) or wrong value
       types (e.g. non-integer `log_rotation_mb`) — do not silently fall back on parse
       errors, only on a missing file.
     - Return a fully populated `Settings`.
     - **Implementation note**: `db_file_path == ":memory:"` is special-cased and skipped
       during path resolution (not passed through `Path(...).resolve()`), so tests and users
       can still configure an in-memory SQLite database via `config.toml` or the env
       override.
4.2. [x] Update `bootstrap/logging_config.py` to accept/consume `Settings` (or the four logging
     fields) instead of calling `os.getenv("NWTRACK_LOG_FILE", ...)` etc. directly, so
     `load_settings()` is the single source of truth for all configuration.
     **Implementation**: `setup_logging(settings: Settings) -> None` now takes `Settings` as
     a required parameter rather than reading the environment itself.
4.3. [x] Update the composition roots (`bootstrap/composition.py`, `bootstrap/tui_composition.py`)
     and wherever `logging_config` is invoked at startup to thread the loaded `Settings`
     through instead of relying on ambient environment state.
     **Implementation note**: `bootstrap/composition.py` and `bootstrap/tui_composition.py`
     needed no changes — both already resolved `Settings` via `load_settings()` through the
     DI container. The 22 use-case `main()` functions and `entrypoints/cli/commands/tui.py`
     (all of which previously called bare `load_dotenv(); setup_logging()`) were updated to
     `settings = load_settings(); setup_logging(settings)` instead.
     **Test isolation note** (supports validation, not in original plan): added an
     `autouse` fixture `_isolate_config_env` in `tests/conftest.py` that sets
     `NWTRACK_DATABASE__DB_FILE_PATH=:memory:` and a tmp-path `NWTRACK_LOGGING__LOG_FILE`
     for every test. Without it, CLI smoke tests that invoke the real `app.py` callback
     (which always calls `load_settings()`) would read/write real files under the
     developer's home directory during test runs, since defaults are no longer `:memory:`.

## 5. `nwtrack config init` command

5.1. Define an `InitConfigPresenter` Protocol in `application/ports/presentation.py`
     (`show_target_path`, `confirm_overwrite`, `show_success`, `show_cancelled`) following
     the existing presenter-protocol pattern.
5.2. Implement `RichInitConfigPresenter` in `entrypoints/cli/adapters/` using
     `rich.prompt.Confirm`, matching the style in `db_admin_presenters.py`.
5.3. Add an `init_config` use case (`application/use_cases/`) that:
     - Resolves the default config target path (`default_config_dir()/config.toml`).
     - If the file exists, asks the presenter to confirm overwrite; aborts cleanly if
       declined.
     - Writes a default `config.toml` (sectioned, with resolved platformdirs-based default
       paths filled in as comments or literal values — literal values are more useful to a
       first-time editor) to the target path, creating parent directories as needed.
     - Returns `OperationResult[Path]`.
5.4. Add a `config` Typer sub-app (`entrypoints/cli/`) with an `init` command wired to the
     use case, following the existing CLI command-group registration pattern.

## 6. Documentation and example files

6.1. Remove `.env_example`; add `config.example.toml` at the repo root showing the sectioned
     format with commented defaults.
6.2. Update `README.md` (and any `.env`-referencing setup instructions) to describe
     `config.toml`, the search-path order, the env var override names, and
     `nwtrack config init`.
6.3. Update `CLAUDE.md`'s "Environment variables are loaded from `.env`" section to describe
     the new config.toml + env-override model instead (this is the checked-in project
     guidance file, not the spec — update once implementation lands and matches).

## 7. Tests

7.1. Unit tests for `infra/config/paths.py`: search-order precedence (each of the three
     locations, in priority order), and the `None`/missing case.
7.2. Unit tests for `infra/config/load.py`:
     - Loads values correctly from a well-formed `config.toml`.
     - Missing `config.toml` → falls back to defaults without raising.
     - Malformed TOML / wrong types → raises a clear error.
     - Each `NWTRACK_DATABASE__*` / `NWTRACK_LOGGING__*` env var overrides its corresponding
       TOML value.
     - Defaults resolve via `platformdirs` (`default_db_file_path()`, `default_log_file_path()`)
       when a key is absent from `config.toml` and no matching env var is set.
7.3. Tests for the `init_config` use case: writes expected file when none exists; prompts
     and respects confirm/decline via a mock presenter when a file already exists.
7.4. CLI test for `nwtrack config init` wiring (command exists, invokes the use case).
7.5. Update/remove any existing tests that assumed `.env` loading or the old flat
     `NWTRACK_DB_FILE_PATH`-style env vars.

## 8. Cleanup

8.1. Remove all remaining `python-dotenv` imports/usages across the codebase.
8.2. Confirm no other module reads `NWTRACK_*` env vars directly (grep check) — all
     configuration should flow through `Settings`/`load_settings()`.
