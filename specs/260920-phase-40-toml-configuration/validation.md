# Phase 40: TOML-Based Configuration Management — Validation

## Automated

- `just check` (ruff + mypy + pytest) passes with no orphaned `.env`/`python-dotenv`
  references.
- New/updated tests assert:
  - `resolve_config_file()` honors the three-location search order and returns `None` when
    nothing is found (see `plan.md` 7.1).
  - `load_settings()` correctly parses a well-formed `[database]`/`[logging]` `config.toml`
    into `Settings` (see `plan.md` 7.2).
  - `load_settings()` falls back to `platformdirs`-based defaults (not `:memory:` /
    working-directory defaults) when `config.toml` is absent, without raising.
  - `load_settings()` raises a clear error on malformed TOML or wrong value types (e.g.
    `log_rotation_mb = "ten"`), rather than silently coercing or falling back.
  - Each `NWTRACK_DATABASE__DB_FILE_PATH`, `NWTRACK_LOGGING__LOG_FILE`,
    `NWTRACK_LOGGING__LOG_FILE_LEVEL`, `NWTRACK_LOGGING__LOG_ROTATION_MB`,
    `NWTRACK_LOGGING__LOG_BACKUP_COUNT` env var overrides its corresponding TOML value when
    both are present.
  - `init_config` use case writes a default `config.toml` to
    `platformdirs.user_config_dir("nwtrack")` when none exists.
  - `init_config` use case, via a mock `InitConfigPresenter`, aborts without writing when
    the user declines the overwrite confirmation, and overwrites when they accept.
  - `bootstrap/logging_config.py` no longer calls `os.getenv("NWTRACK_...")` directly —
    logging configuration is sourced entirely from the `Settings` passed in.
  - `grep -rn "NWTRACK_" src/` (or an equivalent test-time check) shows env var names only
    in the new `infra/config/load.py` override logic, not scattered across other modules.
- Existing test suite continues to pass with fixtures updated for the new `Settings` shape
  (`base_config` fixture in `conftest.py` likely needs its constructor call updated to the
  expanded `Settings` fields).

## Manual

1. Fresh checkout, no `config.toml` anywhere on the search path, no relevant `NWTRACK_*` env
   vars set: run any `nwtrack` command (e.g. `nwtrack accounts list`) — confirm it runs
   using in-code/platformdirs defaults and prints/logs guidance naming the three searched
   paths and mentioning `nwtrack config init`.
2. Run `nwtrack config init` — confirm it writes `config.toml` to
   `~/Library/Application Support/nwtrack/config.toml` (macOS) with sectioned
   `[database]`/`[logging]` content and correct platformdirs-derived default paths.
3. Edit the generated `config.toml` (e.g. change `log_file_level` to `DEBUG`) and run a
   command — confirm the change takes effect (check the log file for DEBUG-level output).
4. Run `nwtrack config init` again with the file already present — confirm it prompts for
   confirmation, and declining leaves the existing file untouched (checksum/diff before and
   after).
5. Set `NWTRACK_DATABASE__DB_FILE_PATH` to a different path in the shell and run a command —
   confirm it overrides the `config.toml` value (check `nwtrack admin` output or DB file
   written to the overridden path).
6. Place a `config.toml` at `~/.config/nwtrack/config.toml` only (no file at the
   `platformdirs` default location) — confirm it is found and used, validating the fallback
   search order.
7. Place a `config.toml` at `./config/nwtrack/config.toml` (project-relative) only — confirm
   it is found and used as the final fallback.
8. Put invalid TOML (or a non-integer `log_rotation_mb`) in `config.toml` — confirm
   `nwtrack` exits with a clear, actionable error message rather than a raw traceback or
   silent fallback.
9. Confirm `.env` files are fully ignored — put a `NWTRACK_DB_FILE_PATH` (old-style, no
   `DATABASE__` prefix) in a `.env` file at the repo root and confirm it has no effect.
10. Confirm the TUI (`nwtrack tui launch`) also picks up `config.toml` settings (database
    path, log level) — not just the CLI path.

## Tone check

- `config init` guidance messages and error text follow the existing Rich presenter style
  (`[bold]`/`[error]`/`[label]` markup conventions already used in
  `entrypoints/cli/adapters/`), not a new ad-hoc format.
- README and `config.example.toml` copy is consistent with existing setup-instruction tone
  (`README.md`'s current `.env` section as the baseline).

## Definition of done

- All `NWTRACK_*` settings load from `config.toml` via `platformdirs`-resolved search paths,
  with env var overrides working under their renamed, section-based names.
- `.env` loading and the `python-dotenv` dependency are fully removed.
- `nwtrack config init` exists, is documented, and behaves per `requirements.md` (refuse to
  silently overwrite; confirm first).
- `README.md`, `CLAUDE.md`, and `config.example.toml` reflect the new configuration model;
  `.env_example` is removed.
- `ruff`, `mypy`, and `pytest` (`just check`) all pass.
- Manual validation steps 1–10 above are performed and confirmed on macOS.
