# Plan: Config Search Order and Path

## 1. Search order — DONE

1. In `infra/config/paths.py`, reorder `config_search_paths()` to
   `./config/nwtrack`, `~/.config/nwtrack`, then `default_config_dir()`.
2. Update the docstrings that say "highest-priority" (`default_config_dir` is now the
   *lowest*-priority location but still the `config init` default write target).

## 2. Override holder and resolution — DONE

1. In `paths.py`, add a small process-level override: a frozen dataclass
   `ConfigFileOverride(path: Path, source: ConfigFileOverrideSource)` where the source enum
   has `FLAG` and `ENV`, plus `set_config_file_override(override | None)` and
   `get_config_file_override()`.
2. `resolve_config_file()`: if an override is set, return its path if it is a file, else raise
   a `ConfigFileNotFoundError` (new `ValueError` subclass) whose message names the path and the
   source. Otherwise fall through to the search path.
3. `config_search_paths()` is unchanged by the override (it still lists the standard
   candidates for display).

## 3. CLI wiring — DONE

1. In `entrypoints/cli/app.py`, add to the root callback:
   `config_file: Path | None = typer.Option(None, "--config-file", envvar="NWTRACK_CONFIG_FILE", help=...)`.
   Treat an empty value as unset.
2. Use `ctx.get_parameter_source("config_file")` to pick `FLAG` vs `ENV`; expand `~` and
   resolve the path.
3. Call `set_config_file_override(...)` **before** `_ensure_runtime_schema()` (which already
   calls `load_settings()`), and clear it when none is given so repeated in-process invocations
   (tests) don't leak state.
4. Catch `ConfigFileNotFoundError` around schema setup and exit 1 with the message via the
   existing console/error style; no traceback.
5. `config init` and `config show` run through the same callback; make sure a missing override
   file does not block `config init` (see group 5.2).

## 4. `config show` — DONE

1. Extend `ConfigShowResult` in `application/dto.py` with an optional
   `override: ConfigFileOverrideInfo | None` (path, source label, exists).
2. `describe_settings()` populates it from the holder; no search path is `is_active` when an
   override is in effect; the missing-override case is reported rather than raised.
3. Update `RichShowConfigPresenter` (`entrypoints/cli/adapters/config_presenters.py`) to print
   a "Config file override: <path> (from --config-file | NWTRACK_CONFIG_FILE)" line above the
   search-path table, and the order shown is the new one.

## 5. `config init` — DONE

1. `InitConfig.run()`: target = override path if set, else
   `default_config_dir() / "config.toml"`.
2. Skip the missing-file check for the override target (init creates it); create parent dirs.
3. Skip the shadow prompt when an override is set. Otherwise keep it, but reword
   `confirm_shadow` in the protocol and Rich adapter so it says the new file will be *ignored*
   because a higher-priority file is in effect (`resolve_config_file()` result, compared with
   the target).

## 6. Docs — DONE

1. `CLAUDE.md` Database Operations/config paragraph, `specs/tech-stack.md` Configuration
   Model, `config.example.toml`, `README.md`: new order, `--config-file`, `NWTRACK_CONFIG_FILE`,
   precedence.
2. `CHANGELOG.md`: entry including the order-change note.

## 7. Tests — DONE (written alongside groups 1–5)

1. `tests/infra/config/test_paths.py`: update order test and the three fallback tests for the
   reversed order; add override tests (file exists, missing -> error naming source).
2. `tests/infra/config/test_load.py`: `describe_settings()` reports override and no active
   search path; load reads settings from the override file.
3. `tests/use_cases/test_init_config.py` / `test_show_config.py`: override target, no shadow
   prompt under override, reworded shadow prompt, override section in show output.
4. CLI tests (`tests/entrypoints/`): `--config-file` beats `NWTRACK_CONFIG_FILE`; env alone
   works; missing file exits non-zero with the message; override state doesn't leak between
   tests (add an autouse reset to `conftest.py`, and make `_isolate_config_env` also unset
   `NWTRACK_CONFIG_FILE`).
