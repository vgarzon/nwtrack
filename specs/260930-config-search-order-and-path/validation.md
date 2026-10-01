# Validation: Config Search Order and Path

## Automated

Quality gates (all must pass): `just lint`, `just typecheck`, `just test` (or `just check`).

Specific assertions required:

- `config_search_paths()` returns, in order: `./config/nwtrack/config.toml`,
  `~/.config/nwtrack/config.toml`, `user_config_dir("nwtrack")/config.toml`.
- `resolve_config_file()` with files present at all three locations returns the `./config`
  one; with only the home and platformdirs ones returns the home one; with only platformdirs
  returns that; with none returns `None`.
- With an override set to an existing file, `resolve_config_file()` returns it even when
  search-path files exist; `load_settings()` reads values from it.
- With an override set to a missing path, `resolve_config_file()` raises
  `ConfigFileNotFoundError` whose message contains the path and `--config-file` or
  `NWTRACK_CONFIG_FILE` according to source. There is no fallback to the search path.
- CLI: `--config-file A` with `NWTRACK_CONFIG_FILE=B` uses A; env alone uses B; empty env
  value is ignored; a missing file exits non-zero with no traceback.
- `describe_settings()` under an override exposes the override path/source and marks no
  search path active.
- `InitConfig` writes to the override path when set (creating parent dirs and succeeding even
  though the file doesn't exist yet), shows no shadow prompt under an override, and otherwise
  targets `default_config_dir()`; the reworded shadow prompt is shown when a higher-priority
  file is in effect.
- Override state is cleared between tests (no cross-test leakage); the autouse isolation
  fixture unsets `NWTRACK_CONFIG_FILE` so a developer's shell value can't affect the suite.

## Manual

Use a scratch directory and a throwaway `db_file_path` in each config so no real data is touched.

1. `nwtrack config show` with only the standard-location file present: it is active, listed
   last in the search order.
2. Add `~/.config/nwtrack/config.toml` (different `log_file_level`): `config show` now marks it
   active. Add `./config/nwtrack/config.toml`: that one wins.
3. `nwtrack --config-file /tmp/x.toml config show` shows the override as active with source
   "--config-file"; no search path is marked active.
4. `NWTRACK_CONFIG_FILE=/tmp/x.toml nwtrack config show` shows source "NWTRACK_CONFIG_FILE";
   adding `--config-file /tmp/y.toml` switches to y.
5. `nwtrack --config-file /tmp/missing.toml accounts list` exits non-zero with a one-line
   message naming the path and the flag; the same via env names the env var.
6. `nwtrack --config-file /tmp/new.toml config init` creates the file with no shadow prompt;
   then `nwtrack --config-file /tmp/new.toml config show` reads it.
7. `nwtrack --config-file /tmp/x.toml tui launch` starts the TUI against the db named in x.toml.
8. Edge cases: `~` in the flag value expands; a relative path resolves against the cwd; a
   directory instead of a file is an error; invalid TOML in the override gives the existing
   parse error naming that file.

## Definition of done

- All automated assertions above pass and `ruff`, `mypy`, `pytest` are clean.
- Manual steps 1-8 verified.
- `CLAUDE.md`, `specs/tech-stack.md`, `config.example.toml`, `README.md` describe the new order
  and override; `CHANGELOG.md` has an entry noting the order change.
- Backlog item removed, spec archived to `specs/archive/config-search-order-and-path/`.
