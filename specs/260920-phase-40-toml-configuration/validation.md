# Phase 40: TOML-Based Configuration Management — Validation

## Automated [x]

- [x] `just check` (ruff + mypy + pytest) passes with no orphaned `.env`/`python-dotenv`
  references. Confirmed: 413 tests passed, ruff and mypy clean, zero `dotenv` matches in
  `src/`.
- New/updated tests assert:
  - [x] `resolve_config_file()` honors the three-location search order and returns `None`
    when nothing is found (`tests/infra/config/test_paths.py`, see `plan.md` 7.1).
  - [x] `load_settings()` correctly parses a well-formed `[database]`/`[logging]`
    `config.toml` into `Settings` (`tests/infra/config/test_load.py`, see `plan.md` 7.2).
  - [x] `load_settings()` falls back to `platformdirs`-based defaults (not `:memory:` /
    working-directory defaults) when `config.toml` is absent, without raising.
  - [x] `load_settings()` raises a clear error on malformed TOML or wrong value types (e.g.
    `log_rotation_mb = "ten"`), rather than silently coercing or falling back.
  - [x] Each `NWTRACK_DATABASE__DB_FILE_PATH`, `NWTRACK_LOGGING__LOG_FILE`,
    `NWTRACK_LOGGING__LOG_FILE_LEVEL`, `NWTRACK_LOGGING__LOG_ROTATION_MB`,
    `NWTRACK_LOGGING__LOG_BACKUP_COUNT` env var overrides its corresponding TOML value when
    both are present.
  - [x] `init_config` use case writes a default `config.toml` to
    `platformdirs.user_config_dir("nwtrack")` when none exists
    (`tests/use_cases/test_init_config.py`).
  - [x] `init_config` use case, via a mock `InitConfigPresenter`, aborts without writing when
    the user declines the overwrite confirmation, and overwrites when they accept.
  - [x] `bootstrap/logging_config.py` no longer calls `os.getenv("NWTRACK_...")` directly —
    logging configuration is sourced entirely from the `Settings` passed in. Confirmed by
    code inspection: `setup_logging(settings: Settings)` reads only from `settings.*`.
  - [x] `grep -rn "NWTRACK_" src/` shows env var names only in `infra/config/load.py`'s
    override logic, not scattered across other modules.
- [x] Existing test suite continues to pass with fixtures updated for the new `Settings`
  shape (`base_config` in `conftest.py`, plus 5 other direct `Settings(...)` construction
  sites across `tests/use_cases/test_import_tables_csv.py` and
  `tests/services/test_db_admin_service.py`).
- **CLI wiring test** (`tests/entrypoints/test_cli_config.py`): `nwtrack config --help`
  registers the group; `nwtrack config init` invokes the use case's `main()`.
- **Test isolation**: added `tests/conftest.py`'s autouse `_isolate_config_env` fixture so
  the suite never touches real platformdirs paths under the developer's home directory (see
  `plan.md` 4.3).

## Manual [x] — all 10 steps performed 2026-09-20, isolated `$HOME`/cwd per step

1. [x] Fresh checkout, no `config.toml` anywhere on the search path, no relevant `NWTRACK_*`
   env vars set: run any `nwtrack` command (e.g. `nwtrack accounts list`) — confirm it runs
   using in-code/platformdirs defaults and prints/logs guidance naming the three searched
   paths and mentioning `nwtrack config init`. **Confirmed.**
2. [x] Run `nwtrack config init` — confirm it writes `config.toml` to
   `~/Library/Application Support/nwtrack/config.toml` (macOS) with sectioned
   `[database]`/`[logging]` content and correct platformdirs-derived default paths.
   **Confirmed.**
3. [x] Edit the generated `config.toml` (e.g. change `log_file_level` to `DEBUG`) and run a
   command — confirm the change takes effect. **Confirmed** by re-loading settings and
   asserting `log_file_level == "DEBUG"` (no DEBUG-level log statements exist in the code
   path exercised, so the log file itself has nothing to grep — verified the loaded value
   directly instead).
4. [x] Run `nwtrack config init` again with the file already present — confirm it prompts for
   confirmation, and declining leaves the existing file untouched (checksum/diff before and
   after). **Confirmed** — MD5 identical before/after decline.
5. [x] Set `NWTRACK_DATABASE__DB_FILE_PATH` to a different path in the shell and run a
   command — confirm it overrides the `config.toml` value. **Confirmed.**
6. [x] Place a `config.toml` at `~/.config/nwtrack/config.toml` only (no file at the
   `platformdirs` default location) — confirm it is found and used, validating the fallback
   search order. **Confirmed.**
7. [x] Place a `config.toml` at `./config/nwtrack/config.toml` (project-relative) only, with
   `db_file_path = "./data/sqlite/nwtrack.db"` and `log_file = "logs/nwtrack.log"` — confirm
   it is found and used as the final fallback, and that the DB/log files are created
   relative to the current working directory (not relative to `./config/nwtrack/`), matching
   the current in-repo layout. **Confirmed** — this is the exact scenario that originally
   motivated documenting relative-path resolution in `requirements.md`.
8. [x] Put invalid TOML (or a non-integer `log_rotation_mb`) in `config.toml` — confirm
   `nwtrack` exits with a clear, actionable error message rather than a raw traceback or
   silent fallback. **Finding & fix**: initially this surfaced a full Rich-formatted Python
   traceback (the final line had the clear message, but it wasn't "rather than a raw
   traceback" as required). Fixed by wrapping the CLI entry point
   (`entrypoints/cli/main.py`'s `main()`) in a `try/except ValueError` that prints
   `Configuration error: <message>` to stderr and exits 1 — this also covers `nwtrack tui
   launch`, which goes through the same `app()` call. Covered by
   `tests/entrypoints/test_cli_main.py`. Re-verified manually after the fix: clean one-line
   message, exit code 1, no traceback.
9. [x] Confirm `.env` files are fully ignored — put a `NWTRACK_DB_FILE_PATH` (old-style, no
   `DATABASE__` prefix) in a `.env` file at the repo root and confirm it has no effect.
   **Confirmed.**
10. [x] Confirm the TUI (`nwtrack tui launch`) also picks up `config.toml` settings (database
    path, log level) — not just the CLI path. **Confirmed by code inspection** (Textual's
    interactive event loop isn't practical to drive headlessly here):
    `entrypoints/cli/commands/tui.py`'s `launch()` calls the same `load_settings()` /
    `setup_logging()` as every CLI use case, and `build_tui_container()` →
    `build_base_container()` registers `Settings` via the same `load_settings()` provider
    used for `SQLiteSessionManager`.

**Unrelated finding**: a stray, `.gitignore`d `./config/nwtrack/config.toml` (byte-identical
to `config.example.toml`) was found in the working tree at the start of this validation pass
and removed — its origin is unclear (not created by any committed change), but since
`/config` is gitignored it was never going to reach the PR either way.

## Tone check

- [x] `config init` guidance messages and error text follow the existing Rich presenter
  style (`[bold]`/`[label]`/`[success]`/`[cancel]` markup conventions already used in
  `entrypoints/cli/adapters/`), not a new ad-hoc format.
- [x] README and `config.example.toml` copy is consistent with existing setup-instruction
  tone.

## Definition of done — all met

- [x] All `NWTRACK_*` settings load from `config.toml` via `platformdirs`-resolved search
  paths, with env var overrides working under their renamed, section-based names.
- [x] `.env` loading and the `python-dotenv` dependency are fully removed.
- [x] `nwtrack config init` exists, is documented, and behaves per `requirements.md` (refuse
  to silently overwrite; confirm first).
- [x] `README.md`, `CLAUDE.md`, and `config.example.toml` reflect the new configuration
  model; `.env_example` is removed.
- [x] `ruff`, `mypy`, and `pytest` (`just check`) all pass — 414 tests.
- [x] Manual validation steps 1–10 above are performed and confirmed on macOS.
- [x] **Beyond original scope, found during final validation**: config-loading errors
  (malformed TOML, wrong value types) now exit cleanly with `Configuration error: <message>`
  and exit code 1, instead of an unhandled traceback — `entrypoints/cli/main.py` wraps
  `app()` in a `try/except ValueError`, covering both the CLI and `nwtrack tui launch`.
