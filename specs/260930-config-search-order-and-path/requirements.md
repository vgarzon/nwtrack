# Requirements: Config Search Order and Path

## Problem

The standard per-OS config location (`~/Library/Application Support/nwtrack/` on macOS) is
searched first, so it always wins when present. Because that location is the expected default
(and the write target of `config init`), a user cannot select an alternative config file just
by placing one in a more specific location, and there is no way to point at an arbitrary file.

## Scope

### In scope

1. **Reverse the search order** of `config.toml` candidates (first found wins):

   | Priority | Location |
   |---|---|
   | 1 | `./config/nwtrack/config.toml` (working-directory-relative) |
   | 2 | `~/.config/nwtrack/config.toml` |
   | 3 | `platformdirs.user_config_dir("nwtrack")/config.toml` (standard default) |

2. **Explicit config file override**, which bypasses the search path entirely:
   - Top-level CLI option: `nwtrack --config-file path/to/config.toml <command> <subcommand>`
   - Environment variable: `NWTRACK_CONFIG_FILE=/path/to/config.toml nwtrack <command> ...`
   - Precedence: `--config-file` > `NWTRACK_CONFIG_FILE` > search path.
   - Applies to every command, including `nwtrack tui launch`.

3. **`config show`** reports the override: the active file is the override path, annotated with
   its source (flag or env); the search-path listing is still shown (none marked active when an
   override is in effect).

4. **`config init`** writes to the override path when one is given, otherwise to the standard
   per-OS user dir (unchanged). The existing shadow warning is kept, recomputed against the new
   order (see Decisions).

### Out of scope

- Merging multiple config files (still exactly one file is read).
- Changing the per-setting `NWTRACK_<SECTION>__<KEY>` env overrides or their precedence over
  file values.
- Changing the file format or any setting.
- Adding a `--config-file` option to individual subcommands (top-level only).

## Decisions

1. **Missing override file is a hard error.** If `--config-file`/`NWTRACK_CONFIG_FILE` names a
   path that is not an existing file, the command exits non-zero with a message naming the
   path and where it came from (flag or env). No fallback to the search path, so a typo cannot
   silently load a different config. Exception: `config init`, which may create the file at
   the override path.
   *(Interview answer: "Hard error", extended with the `config init` exception because init
   must be able to create the file it is pointed at.)*

2. **`config init` honors the override, else the user dir.** The target is the override path
   if set, otherwise `default_config_dir()/config.toml`. The shadow prompt fires when the
   target does not exist and a *different* file is currently in effect that the new file would
   not replace. With the reversed order, writing to the user dir (lowest priority) will
   usually be shadowed by a higher-priority file; this is the same condition as today
   (`active_path is not None and active_path != target`) but the message wording must say the
   new file would be *ignored*, not that it would *shadow* the active one. When an override is
   set, the override is by definition the file in effect, so no shadow prompt is shown.

3. **Wiring.** `--config-file` is a Typer root-callback option declared with
   `envvar="NWTRACK_CONFIG_FILE"`, so flag-over-env precedence comes from Typer itself and
   `ctx.get_parameter_source()` distinguishes flag from env for reporting. Roughly 25 use-case
   `main()` functions call `load_settings()` with no arguments, so instead of threading a
   parameter through all of them, the callback records the override once in a process-level
   holder in `infra/config/paths.py` (path + source) *before* `_ensure_runtime_schema()` runs.
   `resolve_config_file()` and `config_search_paths()` consult that holder. This deviates from
   "pass explicitly" only to avoid touching every use case; tests must reset the holder.

4. **Path handling.** The override path is expanded (`~`) and resolved against the current
   working directory at process start, consistent with other relative paths in the config.
   Empty string for the env var is treated as unset (consistent with `db_file_path`/`log_file`
   env handling).

## Context

- Existing code: `infra/config/paths.py` (`config_search_paths`, `resolve_config_file`,
  `default_config_dir`), `infra/config/load.py` (`_resolve`, `describe_settings`),
  `application/use_cases/init_config.py`, `application/use_cases/show_config.py`,
  `entrypoints/cli/app.py` (root `@app.callback()`), `entrypoints/cli/commands/config.py`,
  `entrypoints/cli/adapters/config_presenters.py`, `application/dto.py`
  (`ConfigShowResult`, `ConfigPathInfo`).
- Typer stays (CLI retirement is a separate backlog idea); the TUI is launched through the CLI
  (`nwtrack tui launch`) so it inherits the override with no TUI-specific code.
- **Behavior change to document:** anyone with a `./config/nwtrack/config.toml` in their
  working directory, or `~/.config/nwtrack/config.toml`, now has it take priority over the
  standard location where previously the standard one won. Call this out in `CHANGELOG.md`
  and update `CLAUDE.md`, `specs/tech-stack.md` (Configuration Model), `config.example.toml`
  and `README.md` where they state the order.
- No schema change, so no Alembic revision.
