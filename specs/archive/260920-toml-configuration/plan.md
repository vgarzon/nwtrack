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

## 5. `nwtrack config init` command [x]

5.1. [x] Define an `InitConfigPresenter` Protocol in `application/ports/presentation.py`
     (`show_target_path`, `confirm_overwrite`, `show_success`, `show_cancelled`) following
     the existing presenter-protocol pattern.
5.2. [x] Implement `RichInitConfigPresenter` in `entrypoints/cli/adapters/config_presenters.py`
     using `rich.prompt.Confirm`, matching the style in `db_admin_presenters.py`.
5.3. [x] Add an `init_config` use case (`application/use_cases/init_config.py`, class
     `InitConfig`) that:
     - Resolves the default config target path (`default_config_dir()/config.toml`).
     - If the file exists, asks the presenter to confirm overwrite; aborts cleanly if
       declined.
     - Writes a default `config.toml` (sectioned, with resolved platformdirs-based default
       paths filled in as literal values — chosen over comments since a first-time editor
       benefits more from seeing real resolved values to edit than commented-out examples)
       to the target path, creating parent directories as needed.
     - Returns `OperationResult[Path]`.
     - **Implementation note**: `main()` intentionally does *not* call
       `build_base_container()`/`load_settings()`/`setup_logging()` — config init is a
       bootstrapping command that must work before any config or database exists, so it
       only wires a `Console` + presenter, no DB/Settings dependency.
5.4. [x] Add a `config` Typer sub-app (`entrypoints/cli/app.py`, command module
     `entrypoints/cli/commands/config.py`) with an `init` command wired to the use case,
     following the existing CLI command-group registration pattern. Manually verified: fresh
     `config init` writes the expected sectioned file with resolved default paths; a second
     `config init` prompts and correctly no-ops on decline; a subsequent `accounts list`
     picks up the written `config.toml` (DB and log file created at the configured paths).

## 6. Documentation and example files [x]

6.1. [x] Remove `.env_example`; add `config.example.toml` at the repo root showing the
     sectioned format with commented defaults.
6.2. [x] Update `README.md` (and any `.env`-referencing setup instructions) to describe
     `config.toml`, the search-path order, the env var override names, and
     `nwtrack config init`. Added a new "Configuration" section between "Installation" and
     "Usage".
6.3. [x] Update `CLAUDE.md`'s "Environment variables are loaded from `.env`" section to
     describe the new config.toml + env-override model instead. Also updated the stale
     "SQLite database (default: `data/sqlite/nwtrack.db`)" line under Database Operations,
     since the default is now platformdirs-based rather than a fixed repo-relative path.
     **Beyond original plan scope**: also added a "Configuration Model" section to
     `specs/tech-stack.md` (new default-implementation-choices section, between "Storage
     Model" and "Domain Model Defaults") documenting the TOML/platformdirs/env-override
     model as a standing tech-stack decision, and added `/config` to `.gitignore` (a
     repo-relative `config.toml` under `./config/nwtrack/` is a local dev file, not meant to
     be committed).

## 7. Tests [x]

7.1. [x] Unit tests for `infra/config/paths.py` (`tests/infra/config/test_paths.py`, 6
     tests): search-order precedence (each of the three locations, in priority order), and
     the `None`/missing case.
7.2. [x] Unit tests for `infra/config/load.py` (`tests/infra/config/test_load.py`, 9 tests):
     - Loads values correctly from a well-formed `config.toml`.
     - Missing `config.toml` → falls back to defaults without raising.
     - Malformed TOML / wrong types → raises a clear error.
     - Each `NWTRACK_DATABASE__*` / `NWTRACK_LOGGING__*` env var overrides its corresponding
       TOML value.
     - Defaults resolve via `platformdirs` (`default_db_file_path()`, `default_log_file_path()`)
       when a key is absent from `config.toml` and no matching env var is set.
7.3. [x] Tests for the `init_config` use case (`tests/use_cases/test_init_config.py`, 3
     tests): writes expected file when none exists; prompts and respects confirm/decline via
     a mock presenter when a file already exists.
7.4. [x] CLI test for `nwtrack config init` wiring (`tests/entrypoints/test_cli_config.py`,
     2 tests: command exists, invokes the use case's `main()`).
7.5. [x] Update/remove any existing tests that assumed `.env` loading or the old flat
     `NWTRACK_DB_FILE_PATH`-style env vars. **Finding**: none existed (grep found zero
     matches) — no test previously exercised config loading directly. The 5
     `Settings(db_file_path=...)` construction sites (`tests/conftest.py`,
     `tests/use_cases/test_import_tables_csv.py` x2, `tests/services/test_db_admin_service.py`
     x2) were updated in task group 4's commit to supply the new required logging fields.
     393 → 413 tests total (20 new).

## 8. Cleanup [x]

8.1. [x] Remove all remaining `python-dotenv` imports/usages across the codebase. Verified:
     `grep -rn "dotenv" src/` returns nothing; `python-dotenv` absent from `pyproject.toml`
     and `uv.lock`.
8.2. [x] Confirm no other module reads `NWTRACK_*` env vars directly (grep check) — all
     configuration should flow through `Settings`/`load_settings()`. Verified: `grep -rn
     "NWTRACK_" src/` matches only `infra/config/load.py`.

## 9. Final validation fix (found during manual validation, not in original plan) [x]

9.1. [x] `entrypoints/cli/main.py`'s `main()` now wraps `app()` in `try/except ValueError`,
     printing `Configuration error: <message>` to stderr and exiting 1, instead of letting a
     `load_settings()` error (malformed TOML, wrong value type) surface as a full unhandled
     Rich traceback. Covers both the CLI and `nwtrack tui launch` (both go through `app()`).
     Added `tests/entrypoints/test_cli_main.py`. See `validation.md` manual step 8 for the
     finding that prompted this.

## 10. Addendum: `config init` shadow protection + `config show` [x]

See `requirements.md`'s Addendum section for the full rationale (post-merge review found
`config init` could silently shadow an active lower-priority config with no warning).

10.1. [x] `application/dto.py`: added `ConfigValueSource` (`StrEnum`: `env`/`file`/`default`),
      `ConfigPathInfo` (path/exists/is_active), `ConfigFieldInfo` (name/value/source),
      `ConfigShowResult` (search_paths + fields).
10.2. [x] `infra/config/load.py`: refactored `load_settings()`'s body into a private
      `_resolve() -> tuple[Settings, dict[str, ConfigValueSource]]` shared by `load_settings()`
      (discards sources) and the new `describe_settings() -> ConfigShowResult` (keeps
      sources, adds search-path existence/active flags via `config_search_paths()` +
      `resolve_config_file()`).
10.3. [x] `application/ports/presentation.py`: added `InitConfigPresenter.confirm_shadow(target_path,
      shadowed_path) -> bool`, and a new `ShowConfigPresenter` protocol
      (`display_search_paths`, `display_settings`).
10.4. [x] `application/use_cases/init_config.py`: `InitConfig.run()` now branches — if the
      target path already exists, unchanged overwrite-confirm flow; else, checks
      `resolve_config_file()` and if it finds a different existing path, calls
      `confirm_shadow()` before writing.
10.5. [x] `application/use_cases/show_config.py` (new): `ShowConfig` use case calls
      `describe_settings()` and hands the result to the presenter's two display methods.
      `main()` follows the same no-DB-dependency pattern as `init_config.py`'s `main()`
      (read-only diagnostic command, no `build_base_container()`/`setup_logging()`).
10.6. [x] `entrypoints/cli/adapters/config_presenters.py`: `RichInitConfigPresenter.confirm_shadow`
      (warns which file is in effect, then `Confirm.ask`); new `RichShowConfigPresenter`
      rendering two Rich tables (`Config Search Paths`: Priority/Path/Exists/Active; and
      `Effective Settings`: Setting/Value/Source — source values styled `config.toml` /
      `[warning]env var[/warning]` / `[info]default[/info]`).
10.7. [x] `entrypoints/cli/commands/config.py`: added `config show` command, mirroring the
      `config init` wiring pattern.
10.8. [x] Tests: `tests/use_cases/test_init_config.py` — added `confirm_shadow` to
      `MockInitConfigPresenter`, fixed `resolve_config_file` mocking gap in existing tests
      (they weren't mocking it before, silently depending on real environment/filesystem
      state — a latent test-isolation bug the shadow-check change surfaced), added
      decline/confirm shadow tests (5 tests total, was 3).
      `tests/infra/config/test_load.py` — 2 new `describe_settings()` tests (source tracking,
      no-active-path case; 17 tests total, was 15).
      `tests/use_cases/test_show_config.py` (new) — 1 test.
      `tests/entrypoints/test_cli_config.py` — added `config show` registration + wiring
      assertions (4 tests total, was 2). 420 tests total (was 414).
10.9. [x] Manual validation: repo-relative `./config/nwtrack/config.toml` scenario — see
      `requirements.md` Addendum "Validation" for the full walkthrough.

## 11. Fresh-install-friendly `db_file_path`/`log_file` defaults

11.1. [x] `infra/config/load.py`: added `_path_is_set()` (key present and non-empty) and
      `_path_value()` (empty-string-aware `_str_value()` wrapper) used only for
      `db_file_path`/`log_file`; `_resolve()`'s source-tracking dict and env-var-override
      block both switched to `_path_is_set()`-style empty-string checks for these two fields
      only (the other three env var checks unchanged).
11.2. [x] `application/use_cases/init_config.py`: `_TEMPLATE` rewritten so `db_file_path`/
      `log_file` are commented out, each preceded by a comment naming the resolved default
      path for that machine.
11.3. [x] `config.example.toml`: added a note that both path keys are optional and the
      checked-in values are a source-checkout example, not a requirement.
11.4. [x] Tests: `tests/infra/config/test_load.py` — 3 new tests (empty string in TOML falls
      back to default; empty-string env override falls back rather than overriding;
      `describe_settings()` reports `default` source for an empty-string TOML value; 20 tests
      total, was 17). `tests/use_cases/test_init_config.py` — asserts the generated template
      contains the commented-out lines.
11.5. [x] Docs: `README.md`, `CLAUDE.md`, and `requirements.md`/`validation.md` addenda
      updated. 423 tests total (was 420).
