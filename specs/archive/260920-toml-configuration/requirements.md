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
- A relative `db_file_path` or `log_file` value written *inside* `config.toml` (e.g.
  `db_file_path = "./data/sqlite/nwtrack.db"`, `log_file = "logs/nwtrack.log"`) resolves
  relative to the current working directory at process start — matching today's `.env`
  behavior exactly, regardless of which of the three locations `config.toml` itself was
  found at. This is what lets a source checkout use a `./config/nwtrack/config.toml` with
  repo-relative `db_file_path`/`log_file` entries and get the same on-disk layout as today.
  It is *not* resolved relative to `config.toml`'s own directory. Absolute paths are used
  as-is.
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

## Addendum: `config init` shadow protection + `config show` (2026-09-21)

Post-merge review of the original design surfaced a gap: `InitConfig` always wrote to the
highest-priority location (`default_config_dir()/config.toml`) and only checked whether a
file already existed *there*. If a user had a config.toml active at a lower-priority
location (e.g. `./config/nwtrack/config.toml`) but nothing yet at the platformdirs location,
running `config init` would silently write a new file that took priority going forward —
the existing, actively-used config would be shadowed with no warning.

Two changes close this gap and add visibility into the resolved configuration:

### Scope

- **`config init` shadow protection**: before writing to a target path where no file
  currently exists, `InitConfig` now also checks `resolve_config_file()`. If that returns a
  different, existing path (a lower-priority config is currently active), the presenter
  warns which file is in effect and prompts for confirmation before proceeding — writing
  anyway is allowed (the new file just becomes authoritative), but it is no longer silent.
  This is in addition to, not a replacement for, the existing overwrite-confirmation when a
  file already exists at the target path itself.
- **New `nwtrack config show` command**: read-only diagnostic command that displays:
  - The config search-path priority order, with each path's existence and whether it is the
    currently active one.
  - The fully-resolved effective `Settings` (same values `load_settings()` would produce),
    with each setting's source (`config.toml`, environment variable override, or built-in
    default) called out explicitly.

### Decisions

- **Effective (resolved) settings, not raw file contents.** Showing the final values
  `nwtrack` will actually use — factoring in env var overrides and defaults — is more useful
  for diagnosing "why is nwtrack using this path" than dumping the raw TOML file, which the
  user can already `cat` themselves.
- **Env var overrides are flagged per-setting**, not just implied by a source column that
  only distinguishes file vs. default. A user debugging unexpected behavior needs to see
  *which* setting an env var is currently clobbering.
- **Shadow protection warns and asks, rather than warning-only or refusing outright** — this
  matches the existing `confirm_overwrite` UX pattern (same presenter, same `Confirm.ask`
  style) rather than introducing a new interaction shape, and still lets a user who
  deliberately wants to promote a config to the higher-priority location do so in one step.
- **Landed as additional commits on the existing `phase-40-toml-config` branch/PR**, not a
  new roadmap phase — this fixes a gap in work that had not yet merged, not new scope.
- **No new presentation port beyond `ShowConfigPresenter`**: source-tracking logic lives in
  `infra/config/load.py` (`describe_settings()`, sharing its config-resolution internals with
  `load_settings()` via a private `_resolve()` helper) and is exposed to the presentation
  layer via new DTOs (`ConfigPathInfo`, `ConfigFieldInfo`, `ConfigShowResult`,
  `ConfigValueSource`) in `application/dto.py`, following the existing pattern of infra
  returning application-layer DTOs (precedent: `infra/persistence/schema.py`).

### Validation

- Unit tests: `InitConfig` shadow-confirm/decline paths
  (`tests/use_cases/test_init_config.py`); `describe_settings()` source-tracking
  (`tests/infra/config/test_load.py`); `ShowConfig` use case
  (`tests/use_cases/test_show_config.py`); CLI wiring for `config show`
  (`tests/entrypoints/test_cli_config.py`).
- Manual: verified end-to-end with a repo-relative `./config/nwtrack/config.toml` active —
  `config show` correctly listed it as the active path with `config.toml`-sourced values;
  `config init` warned about shadowing it, declining left it untouched, confirming wrote the
  higher-priority file and `config show` then reflected the new file as active (with the
  lower-priority file still shown as existing but no longer active); an env var override was
  correctly flagged with source `env var`.

## Addendum: fresh-install-friendly `db_file_path`/`log_file` defaults (2026-09-21)

`config init` previously baked the resolved `platformdirs` default paths for `db_file_path`
and `log_file` directly into the generated `config.toml` as active (uncommented) values. This
worked, but meant a fresh install's config file carried machine-specific absolute paths from
the moment it was created, and there was no way to express "use the default" other than
copying it back out.

### Scope

- `db_file_path` and `log_file` are now optional in `config.toml`: an absent key **or** an
  explicit empty string (`""`) both resolve to the same `platformdirs`-derived default
  (`default_db_file_path()` / `default_log_file_path()`). This applies uniformly wherever
  these two values are sourced — the TOML file and their env var overrides
  (`NWTRACK_DATABASE__DB_FILE_PATH`, `NWTRACK_LOGGING__LOG_FILE`) — so an empty-string env var
  falls back to the file/default rather than clobbering it with an empty path.
- `nwtrack config init`'s generated `config.toml` now writes `db_file_path`/`log_file` as
  commented-out lines, with the resolved default shown alongside as a comment for reference
  (e.g. `# db_file_path = ""` preceded by a comment naming the actual default path on that
  machine). The `[logging]` section's other three keys (`log_file_level`,
  `log_rotation_mb`, `log_backup_count`) are unaffected — they already default cleanly on a
  missing key and don't have a meaningful "empty string" case.
- `config show`'s per-field source reporting reflects this: a config.toml with
  `db_file_path = ""` (or the key absent) reports source `default`, matching the value
  `load_settings()` actually produces.

### Decisions

- **Scoped to the two path fields only**, not generalized to all five settings — an empty
  string has no natural meaning for `log_file_level` (a string enum-like value) or the two
  integer fields, so extending the convention there would trade a real fresh-install pain
  point for an inconsistency with no corresponding benefit.
- **Comment out rather than omit the keys entirely** from the `config init` template — this
  keeps the option discoverable and documents the resolved default inline, at the cost of a
  couple of extra comment lines the user can freely delete.
- **Landed as additional commits on the existing `phase-40-toml-config` branch/PR**, same
  rationale as the prior addendum: this refines fresh-install ergonomics for work that has
  not yet merged.

### Validation

- Unit tests: `tests/infra/config/test_load.py` (empty-string-in-file and
  empty-string-env-override both fall back to default; `describe_settings()` reports
  `default` source for an empty-string TOML value); `tests/use_cases/test_init_config.py`
  (generated template contains the commented-out `db_file_path = ""` / `log_file = ""`
  lines).
- Manual: fresh `$HOME`, empty working directory, no `config.toml` anywhere — `config init`
  wrote a config with both path keys commented out; `config show` immediately after showed
  both `db_file_path` and `log_file` resolved to their `platformdirs` defaults with source
  `default`, confirming no editing is required for the application to work end-to-end on a
  first run.
