# Phase 24 Plan: CSV Presenter Protocol Migration

## Task Groups

---

### [x] Group 1: Presenter Protocol Definitions

Add both Protocol interfaces to `application/ports/presentation.py`.

1.1 Add `ImportTablesCSVPresenter` Protocol after the existing `DBInitCSVPresenter` block.
    Methods: `show_header`, `prompt_for_source_dir`, `show_cancellation`,
    `show_import_success`, `show_error`.

1.2 Add `ExportTablesCSVPresenter` Protocol after `ImportTablesCSVPresenter`.
    Methods: `show_header`, `prompt_for_target_dir`, `confirm_create_directory`,
    `show_creating_directory`, `show_directory_create_error`, `show_directory_not_found_error`,
    `show_not_a_directory_error`, `show_cancellation`, `show_table_exported`, `show_table_skipped`.

1.3 Verify `mypy` passes on `application/ports/presentation.py` with no new errors.

Note: `show_table_exported` uses `csv_path: str` (not `Path`) matching the `str` return type of
`ExportCSV.export_tables_to_dir`.

---

### [x] Group 2: Rich Adapter Implementations

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

---

### [x] Group 3: Refactor `import_tables_csv`

3.1 Update `ImportTablesCSVBase.__init__` to accept `presenter: ImportTablesCSVPresenter`
    instead of `console: Console`. Remove `Console` import and usage from this class.

3.2 Update `ImportTablesCSVInteractive` to use presenter methods throughout.

3.3 Update `ImportTablesCSVCLI` to use presenter methods.

3.4 Update `bootstrap()` to register `RichImportTablesCSVPresenter` instead of `Console`.

3.5 Update `run_interactive()` and `run_cli()` to inject `presenter` instead of `console`.

3.6 Remove `from rich.console import Console` and `from rich.prompt import Prompt` imports.

CLI command (`entrypoints/cli/commands/imports.py`) updated to remove its own `Console`
resolution and mode-announcement prints; the presenter `show_header()` handles all visual output.

---

### [x] Group 4: Refactor `export_tables_csv`

4.1–4.6 Same pattern as Group 3 applied to export use case and CLI command.

Note: `create_target_path` was simplified — it now calls `show_directory_create_error` with the
exception message string rather than composing output inline.

---

### [x] Group 5: Tests

Updated `tests/use_cases/test_import_tables_csv.py`:
- Replaced `Console(record=True)` fixture and `monkeypatch.setattr(Prompt.ask)` approach with
  `MockImportTablesCSVPresenter` stub.
- Added 4 presenter interaction tests covering: interactive happy path, interactive abort,
  CLI happy path, service exception → `show_error`.
- All original business logic tests preserved and updated to use mock presenter.

Updated `tests/use_cases/test_export_tables_csv.py`:
- Replaced `Console` fixture and `monkeypatch` approach with `MockExportTablesCSVPresenter` stub.
- Added 6 presenter interaction tests covering: interactive happy path, interactive abort,
  interactive confirm-create path, CLI happy path, CLI not-a-directory error, CLI missing-dir
  without `--create`, CLI missing-dir with `create=True`.
- All original business logic tests preserved and updated to use mock presenter.

Total: 22 tests across both files, all passing.

---

### [x] Group 6: Quality Gates

- `just lint` — passes (0 errors)
- `just typecheck` — passes (0 errors)
- `just test` — 248 passed
