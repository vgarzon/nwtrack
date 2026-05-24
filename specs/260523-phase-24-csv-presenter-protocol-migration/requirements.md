# Phase 24 Requirements: CSV Presenter Protocol Migration

## Scope

### What this phase does

Migrates `import_tables_csv` and `export_tables_csv` from direct Rich Console/Prompt usage to the
presenter ports-and-adapters pattern already established across the rest of the codebase. This is
a mechanical extraction — no business logic changes, schema changes, or new features.

### What is not included

- Changes to `InitDataService`, `ExportCSV`, or any persistence layer
- New CLI commands or options
- Changes to any already-migrated use case
- TUI adapter implementations (those come in a later phase)

---

## Presenter Protocol Methods

### `ImportTablesCSVPresenter`

Covers all console interactions currently in `ImportTablesCSVBase` and `ImportTablesCSVInteractive`.
The interactive-only methods (`show_header`, `prompt_for_source_dir`, `show_cancellation`) are called
only by the interactive path; the non-interactive CLI path calls only the shared methods.

| Method | Return | Current console call |
|---|---|---|
| `show_header()` | `None` | `console.rule("[header]Import Tables from CSV[/header]")` |
| `prompt_for_source_dir(default: str) -> str` | `str` | `prompt.ask(...)` in `collect_source_dir` |
| `show_cancellation()` | `None` | `console.print("[cancel]CSV import aborted by user.[/cancel]")` |
| `show_import_success(source_dir: Path)` | `None` | `console.print("[success]Imported[/success] CSV tables from ...")` |
| `show_error(message: str)` | `None` | `console.print("[error]Error:[/error] {exc}")` |

### `ExportTablesCSVPresenter`

Covers all console interactions currently in `ExportTablesCSVBase` and `ExportTablesCSVInteractive`
and `ExportTablesCSVCLI`.

| Method | Return | Current console call |
|---|---|---|
| `show_header()` | `None` | `console.rule("[header]Export Tables to CSV[/header]")` |
| `prompt_for_target_dir(default: str) -> str` | `str` | `prompt.ask(...)` in `collect_target_dir` |
| `confirm_create_directory(target_dir: str) -> bool` | `bool` | `confirm.ask(...)` in `collect_target_dir` |
| `show_creating_directory(target_dir: Path)` | `None` | `console.print("[label]Creating directory[/label]: ...")` |
| `show_directory_create_error(target_dir: Path, message: str)` | `None` | `console.print("[error]Error:[/error] Failed to create directory ...")` |
| `show_directory_not_found_error(target_dir: Path)` | `None` | `console.print("[error]Error:[/error] Target directory ... does not exist.")` |
| `show_not_a_directory_error(target_dir: Path)` | `None` | `console.print("[error]Error:[/error] Target path ... is not a directory.")` |
| `show_cancellation()` | `None` | `console.print("[cancel]CSV export aborted by user.[/cancel]")` |
| `show_table_exported(table_name: str, csv_path: Path, n_records: int)` | `None` | `console.print("[success]Exported[/success] {n_records} ...")` |
| `show_table_skipped(table_name: str)` | `None` | `console.print("[info]Skipped empty[/info] ...")` |

---

## Decisions

### Discrete presenter methods

Each distinct console interaction becomes its own presenter method. This mirrors the pattern used by
all 25 existing presenter Protocols and allows TUI adapters to map each interaction to a distinct
widget or event. Coarser groupings like `show_result()` would obscure the individual interactions
and make TUI adaptation harder.

### Preserve the Base/Interactive/CLI class hierarchy

The three-class structure (`Base`, `Interactive`, `CLI`) in each use case is preserved. Collapsing
them would widen the scope of this phase beyond the mechanical presenter extraction it is meant to
be, and risks changing observable behavior. The presenter is injected into `Base`, which passes it
down to the subclasses through `super().__init__()`.

### One presenter Protocol per use case

`ImportTablesCSVPresenter` and `ExportTablesCSVPresenter` are separate Protocols. The interactive
and CLI subclasses both receive the same presenter and call different subsets of its methods — the
non-interactive CLI paths simply never call `prompt_for_*` or `show_cancellation`.

### Minor UX improvements allowed

The Rich adapters may clean up wording inconsistencies relative to other adapters (e.g. aligning
cancel and error message patterns). Functional behavior — prompts, confirmations, directory
creation, import/export outcomes — must remain identical.

### New adapter file: `csv_presenters.py`

Both Rich adapters live in a new file `entrypoints/cli/adapters/csv_presenters.py`, consistent
with the one-file-per-domain naming convention (`balance_presenters.py`, `tag_presenters.py`,
etc.).

### DI wiring

The `bootstrap()`, `run_interactive()`, and `run_cli()` functions in each use case module are
updated to register and inject the presenter instead of `Console`. The `Console` registration is
removed from both bootstrap functions since neither use case accesses it directly after the
refactor.

---

## Context

### Patterns to follow

- Protocol definitions: follow `DBInitCSVPresenter` in `application/ports/presentation.py` (lines
  764–813) as the closest structural reference — it covers a similar CSV-oriented interactive
  workflow with header, prompts, confirmation, cancellation, success, and error methods.
- Rich adapter: follow `RichDBInitCSVPresenter` in `entrypoints/cli/adapters/db_admin_presenters.py`
  as the implementation reference.
- DI wiring: follow how `main()` functions in recently-migrated use cases register the presenter
  class and inject it via the container.

### Stack constraints

No new dependencies. Rich is already in the stack and is the correct library for the adapter
implementations.

### Testing

Tests for both use cases should use mock presenters (plain objects implementing the Protocol
interface) rather than real Rich Console instances. The existing test suite uses this pattern
throughout — see `tests/use_cases/` for reference fixtures.
