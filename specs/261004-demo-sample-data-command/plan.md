# Plan: Demo Sample Data Command

## 1. Sample dataset — DONE

1. Add a module (e.g. `application/services/sample_data.py`) exposing a pure function that
   returns the sample records for a given reference month (currencies, categories,
   institutions, tags, accounts, account-tag links, status history, balances, exchange rates).
   Records are CSV-shaped and load through a new public `InitDataService.import_records()`,
   reusing the proven CSV import path.
2. Keep amounts as integer smallest units; liabilities positive; 12 months ending at the
   reference month; at least one inactive account with status history to match.

## 2. Use case and ports — DONE

1. Add `AdminCreateSampleDbPresenter` Protocol to `application/ports/presentation.py`
   (`show_header`, `show_success(path, summary)`, `show_error(message)`).
2. Add a result DTO (path plus entity counts) to `application/dto.py`.
3. Add `application/use_cases/admin_create_sample_db.py` with `CreateSampleDatabase`:
   - validate target: reject if path exists, reject if parent directory is missing;
   - create schema via `SchemaManager.create_all_tables()` on an engine for `PATH`;
   - insert the dataset in a single UoW transaction;
   - on failure, remove the file this run created and return a failed `OperationResult`.
4. `main(path)` builds a container whose settings/engine/UoW point at `PATH` (not the
   configured database), registers the presenter, runs the use case, returns exit code.

## 3. CLI wiring

1. Add `create-sample-db` to `entrypoints/cli/commands/admin.py` with a required `PATH`
   argument (`typer.Argument`), lazy-importing the use case.
2. Exempt this command from `_ensure_runtime_schema()` in the root callback in
   `entrypoints/cli/app.py` (same mechanism as `config`; compare `ctx.invoked_subcommand`
   and the nested command name so only `admin create-sample-db` is skipped).
3. Exit non-zero on failure.

## 4. Presenter — DONE

1. Add `RichAdminCreateSampleDbPresenter` in `entrypoints/cli/adapters/admin_presenters.py`.
2. Success output: absolute path, dataset summary, `config.toml` snippet, env var
   alternative, and the "configuration not modified" note.

## 5. Tests

1. Dataset: counts, 12 consecutive months ending at the reference month, liabilities in
   liability categories, every account has an institution, status history consistent.
2. Use case (tmp_path): creates file, schema at `head`, data readable through repositories
   and reports (net worth history runs without error); refuses existing file; refuses
   missing parent dir; cleans up on injected failure; existing file content unchanged after
   refusal.
3. CLI (Typer runner, `_isolate_config_env` active): missing `PATH` argument errors; success
   run does not create or modify the configured database; output contains the path and
   `db_file_path` snippet.

## 6. Docs

1. `README.md`: new-user "try it with sample data" section.
2. `CLAUDE.md`: add `admin create-sample-db` to the command list and note the root-callback
   exemption.
3. `CHANGELOG.md`: one-line entry.
