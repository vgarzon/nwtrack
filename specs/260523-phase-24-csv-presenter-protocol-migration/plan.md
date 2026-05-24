# Phase 24 Plan: CSV Presenter Protocol Migration

## Task Groups

---

### Group 1: Presenter Protocol Definitions

Add both Protocol interfaces to `application/ports/presentation.py`.

1.1 Add `ImportTablesCSVPresenter` Protocol after the existing `DBInitCSVPresenter` block.
    Methods: `show_header`, `prompt_for_source_dir`, `show_cancellation`,
    `show_import_success`, `show_error`.

1.2 Add `ExportTablesCSVPresenter` Protocol after `ImportTablesCSVPresenter`.
    Methods: `show_header`, `prompt_for_target_dir`, `confirm_create_directory`,
    `show_creating_directory`, `show_directory_create_error`, `show_directory_not_found_error`,
    `show_not_a_directory_error`, `show_cancellation`, `show_table_exported`, `show_table_skipped`.

1.3 Verify `mypy` passes on `application/ports/presentation.py` with no new errors.

---

### Group 2: Rich Adapter Implementations

Create `entrypoints/cli/adapters/csv_presenters.py` with both Rich adapters.

2.1 Create `RichImportTablesCSVPresenter` implementing `ImportTablesCSVPresenter`.
    - Constructor accepts `Console`.
    - `show_header`: `console.rule("[header]Import Tables from CSV[/header]")`.
    - `prompt_for_source_dir(default)`: `Prompt.ask(...)`, return the string value.
    - `show_cancellation`: `console.print("[cancel]CSV import aborted by user.[/cancel]")`.
    - `show_import_success(source_dir)`: `console.print("[success]Imported[/success] CSV tables from [bold]{source_dir}[/bold]")`.
    - `show_error(message)`: `console.print(f"[error]Error:[/error] {message}")`.

2.2 Create `RichExportTablesCSVPresenter` implementing `ExportTablesCSVPresenter`.
    - Constructor accepts `Console`.
    - `show_header`: `console.rule("[header]Export Tables to CSV[/header]")`.
    - `prompt_for_target_dir(default)`: `Prompt.ask(...)`, return the string value.
    - `confirm_create_directory(target_dir)`: `Confirm.ask(...)`, return bool.
    - `show_creating_directory(target_dir)`: `console.print("[label]Creating directory[/label]: {target_dir}")`.
    - `show_directory_create_error(target_dir, message)`: `console.print("[error]Error:[/error] Failed to create directory ...")`.
    - `show_directory_not_found_error(target_dir)`: `console.print("[error]Error:[/error] Target directory ... does not exist. Use --create to create it.")`.
    - `show_not_a_directory_error(target_dir)`: `console.print("[error]Error:[/error] Target path ... is not a directory.")`.
    - `show_cancellation`: `console.print("[cancel]CSV export aborted by user.[/cancel]")`.
    - `show_table_exported(table_name, csv_path, n_records)`: existing Rich markup from `export_tables_to_dir`.
    - `show_table_skipped(table_name)`: existing Rich markup from `export_tables_to_dir`.

2.3 Export both classes from `entrypoints/cli/adapters/__init__.py` if applicable.

2.4 Verify `mypy` passes on `csv_presenters.py`.

---

### Group 3: Refactor `import_tables_csv`

3.1 Update `ImportTablesCSVBase.__init__` to accept `presenter: ImportTablesCSVPresenter`
    instead of `console: Console`. Remove `Console` import and usage from this class.
    - `import_tables_from_dir`: replace `self._console.print(...)` calls with
      `self._presenter.show_error(str(exc))` and `self._presenter.show_import_success(source_dir)`.

3.2 Update `ImportTablesCSVInteractive.__init__` to pass `presenter` to `super().__init__()`.
    Remove `Prompt` instantiation. Update `run` to call `self._presenter.show_header()` and
    `self._presenter.show_cancellation()`. Update `collect_source_dir` to call
    `self._presenter.prompt_for_source_dir(default=...)` and return the result as a `Path`.

3.3 Update `ImportTablesCSVCLI.__init__` to pass `presenter` to `super().__init__()`. Update
    `run` to call `self._presenter.show_header()`.

3.4 Update `bootstrap()` to register `ImportTablesCSVPresenter` (via `RichImportTablesCSVPresenter`)
    instead of `Console`. Remove `Console` registration and `build_console` import.

3.5 Update `run_interactive()` and `run_cli()` to inject `presenter` instead of `console`.

3.6 Remove `from rich.console import Console` and `from rich.prompt import Prompt` imports.

---

### Group 4: Refactor `export_tables_csv`

4.1 Update `ExportTablesCSVBase.__init__` to accept `presenter: ExportTablesCSVPresenter`
    instead of `console: Console`. Remove `Console` import and usage.
    - `create_target_path`: replace `console.print` calls with
      `self._presenter.show_creating_directory`, `self._presenter.show_directory_create_error`.
    - `export_tables_to_dir`: replace per-table `console.print` calls with
      `self._presenter.show_table_exported` and `self._presenter.show_table_skipped`.

4.2 Update `ExportTablesCSVInteractive.__init__` to pass `presenter` to `super().__init__()`.
    Remove `Prompt` and `Confirm` instantiation. Update `run` to call `show_header` and
    `show_cancellation` via presenter. Update `collect_target_dir` to call
    `self._presenter.prompt_for_target_dir` and `self._presenter.confirm_create_directory`.

4.3 Update `ExportTablesCSVCLI.__init__` to pass `presenter` to `super().__init__()`. Update
    `run` to call `self._presenter.show_header()`. Update `check_or_create_target_dir` to call
    `self._presenter.show_not_a_directory_error` and `self._presenter.show_directory_not_found_error`.

4.4 Update `bootstrap()` to register `ExportTablesCSVPresenter` (via `RichExportTablesCSVPresenter`)
    instead of `Console`. Remove `Console` registration and `build_console` import.

4.5 Update `run_interactive()` and `run_cli()` to inject `presenter` instead of `console`.

4.6 Remove `from rich.console import Console`, `from rich.prompt import Prompt, Confirm` imports.

---

### Group 5: Tests

5.1 Write `tests/use_cases/test_import_tables_csv.py`.
    - Define a `MockImportTablesCSVPresenter` stub implementing all protocol methods, recording
      calls for assertion.
    - Test `ImportTablesCSVInteractive.run()`: happy path imports successfully; presenter
      `show_header`, `prompt_for_source_dir`, and `show_import_success` are called.
    - Test `ImportTablesCSVInteractive.run()`: `KeyboardInterrupt` path calls `show_cancellation`.
    - Test `ImportTablesCSVCLI.run()`: happy path calls `show_header` and `show_import_success`.
    - Test `ImportTablesCSVBase.import_tables_from_dir()`: on service exception, calls `show_error`.

5.2 Write `tests/use_cases/test_export_tables_csv.py`.
    - Define a `MockExportTablesCSVPresenter` stub.
    - Test `ExportTablesCSVInteractive.run()`: happy path calls `show_header`,
      `prompt_for_target_dir`, and at least one of `show_table_exported` / `show_table_skipped`.
    - Test `ExportTablesCSVInteractive.run()`: `KeyboardInterrupt` path calls `show_cancellation`.
    - Test `ExportTablesCSVInteractive.collect_target_dir()`: non-existent dir path calls
      `confirm_create_directory`; if confirmed, calls `show_creating_directory`.
    - Test `ExportTablesCSVCLI.run()`: CLI path with existing dir calls `show_header` and export
      methods.
    - Test `ExportTablesCSVCLI.check_or_create_target_dir()`: non-directory path calls
      `show_not_a_directory_error`; missing dir without `--create` calls
      `show_directory_not_found_error`.

---

### Group 6: Quality Gates

6.1 Run `just lint` — no new ruff errors.
6.2 Run `just typecheck` — no new mypy errors.
6.3 Run `just test` — all tests pass.
