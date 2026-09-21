# Phase 40: TOML-Based Configuration Management — Requirements

## Scope

Replace `.env`-based configuration with a `config.toml` file resolved from standard
per-OS locations via `platformdirs`, covering every setting `nwtrack` currently reads from
the environment. This is a 1:1 replacement of the *source* of configuration, not a new
layered precedence model beyond what exists today (file defaults, overridable by
environment variables).

### In scope

- All current `NWTRACK_*` settings move into `config.toml`:
  - `db_file_path`
  - `log_file`
  - `log_file_level`
  - `log_rotation_mb`
  - `log_backup_count`
- `config.toml` resolution order (first found wins):
  1. `platformdirs.user_config_dir("nwtrack")` — e.g.
     `~/Library/Application Support/nwtrack/` on macOS, `~/.config/nwtrack/` on Linux
     (XDG-aware by default via `platformdirs`)
  2. `~/.config/nwtrack/` — explicit XDG-style fallback for macOS users who prefer it, even
     though `platformdirs`' default on macOS is `Application Support/`
  3. `./config/nwtrack/` — project-relative fallback (matches today's working-directory
     dependence, for running from a source checkout)
- `config.toml` uses grouped sections: `[database]` and `[logging]`.
- Default `db_file_path` and `log_file` resolve via `platformdirs.user_data_dir("nwtrack")`
  and `platformdirs.user_log_dir("nwtrack")` respectively when not explicitly set in
  `config.toml` (e.g. `<user_data_dir>/nwtrack.db`, `<user_log_dir>/nwtrack.log`).
- Shell environment variables continue to override the corresponding `config.toml` values.
  Env var names are renamed to reflect the new section structure using a `__` separator:
  - `NWTRACK_DATABASE__DB_FILE_PATH`
  - `NWTRACK_LOGGING__LOG_FILE`
  - `NWTRACK_LOGGING__LOG_FILE_LEVEL`
  - `NWTRACK_LOGGING__LOG_ROTATION_MB`
  - `NWTRACK_LOGGING__LOG_BACKUP_COUNT`
- `.env` is no longer loaded. `python-dotenv` is removed from dependencies.
- If no `config.toml` is found at any searched location, `nwtrack` falls back to built-in
  defaults and prints/logs guidance listing the paths it searched and how to create one.
- A new `nwtrack config init` CLI command writes a default `config.toml` (with the resolved
  platformdirs-based defaults filled in) to the highest-priority location
  (`user_config_dir("nwtrack")`). If a `config.toml` already exists there, the command
  prompts for confirmation before overwriting.
- `.env_example` is replaced with a `config.toml` example (e.g. `config.example.toml` at
  the repo root), and README configuration instructions are updated accordingly.

### Out of scope (this phase)

- `pydantic`/schema-validation-library adoption — `Settings` stays a plain dataclass;
  `tomllib` (stdlib, Python 3.12+) parses the file and invalid/missing keys raise a clear
  error, but there is no external schema-validation dependency.
- A `version` key in `config.toml` and any migration logic — deferred until a breaking
  schema change is actually needed.
- `cache_dir` / `platformdirs.user_cache_dir` — not wired up; nothing currently needs a
  cache.
- An automated `.env` → `config.toml` migration command — this is a clean cutover; existing
  `.env` users update manually per the README, optionally bootstrapped via
  `nwtrack config init`.
- Moving `db_file_path`/`log_file` *defaults* changes CLI/TUI behavior for anyone currently
  relying on the in-repo `data/sqlite/nwtrack.db` and `./logs/nwtrack.log` defaults; this is
  an intentional, documented breaking change (see Decisions).
- Any TUI screen for editing configuration — `config init` is CLI-only for this phase.

## Decisions

- **No new validation dependency.** Matches `specs/tech-stack.md`'s "keep local workflows
  fast and dependency-light" standard and the user's explicit preference to stay
  dataclass-only rather than adopt `pydantic` for this phase.
- **No schema version key yet.** Versioning adds complexity with no current migration to
  perform; can be introduced later without disrupting this phase's design.
- **`platformdirs` is the only new dependency; `python-dotenv` is removed.** Net dependency
  count is unchanged.
- **Config file structure is sectioned (`[database]`, `[logging]`), not flat.** This scales
  better as settings grow and gives natural grouping for validation error messages.
- **Env var override names change to match the new sections** (`NWTRACK_DATABASE__...`,
  `NWTRACK_LOGGING__...`), using a double-underscore section delimiter — a recognizable
  convention (matches `pydantic-settings`'s nested-env-var delimiter) even though this
  project isn't adopting `pydantic`. This is a breaking rename for the small number of
  people currently setting `NWTRACK_DB_FILE_PATH` etc. as shell env vars; documented in the
  README and covered by tests.
- **Search order intentionally includes both the platformdirs default *and* an explicit
  `~/.config/nwtrack/` fallback,** even though `platformdirs.user_config_dir("nwtrack")`
  already returns an XDG-aware path on Linux. On macOS specifically, `platformdirs`
  defaults to `~/Library/Application Support/nwtrack/`, so the explicit `~/.config/nwtrack/`
  step exists to support macOS users who deliberately prefer XDG-style dotfiles, per the
  user's explicit request. `./config/nwtrack/` remains the final fallback for running from
  a source checkout without any installed config.
- **First run does not silently auto-create `config.toml`.** Auto-creating a file as a side
  effect of just running any command is surprising; instead `nwtrack` uses in-code defaults
  and prints guidance, and file creation is an explicit, discoverable action
  (`nwtrack config init`).
- **`config init` refuses to silently clobber an existing file** — it prompts for
  confirmation, consistent with other destructive-ish CLI interactions in the project
  (e.g. delete confirmations elsewhere in the CLI).

## Context

- Follows the layered architecture: config resolution stays in
  `infra/config/` (`settings.py`, `load.py`), consistent with existing module boundaries.
  `platformdirs` path lookups and `tomllib` parsing belong in infra, not domain/application.
- `Settings` (`infra/config/settings.py`) is currently a minimal frozen dataclass with only
  `db_file_path`; it needs to grow to also carry the logging fields that
  `bootstrap/logging_config.py` currently reads directly via `os.getenv(...)`, so that
  `load_settings()` becomes the single source of truth for all configuration (both DB and
  logging), consistent with the "settings loaded from environment" description in
  `CLAUDE.md`.
- This phase directly sets up Phase 42 (macOS Packaging), which was trimmed during the
  roadmap update to rely on this phase's `platformdirs`-based path resolution rather than
  re-deriving it during packaging.
- `nwtrack config init` should follow the existing CLI command-group pattern (Typer sub-app
  per concern, e.g. `accounts`, `institutions`) and reuse the existing Rich-presenter
  pattern for confirmation prompts (`RichConfirmModal`-equivalent or a simple `Confirm.ask`
  matching other destructive CLI confirmations) rather than introducing a new prompt style.
- No new external dependency beyond `platformdirs`; `tomllib` is stdlib (Python 3.12+, which
  this project already requires).
