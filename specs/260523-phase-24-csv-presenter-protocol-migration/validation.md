# Phase 24 Validation: CSV Presenter Protocol Migration

## Automated Tests

### Required test files

- `tests/use_cases/test_import_tables_csv.py`
- `tests/use_cases/test_export_tables_csv.py`

### Required assertions — import

| Test | Assertion |
|---|---|
| Interactive happy path | `show_header` called once |
| Interactive happy path | `prompt_for_source_dir` called once |
| Interactive happy path | `show_import_success` called with the source directory |
| Interactive abort | `show_cancellation` called; `show_import_success` not called |
| CLI happy path | `show_header` called once; `show_import_success` called |
| Service exception | `show_error` called with a non-empty message; `show_import_success` not called |

### Required assertions — export

| Test | Assertion |
|---|---|
| Interactive happy path (existing dir) | `show_header` called; at least one table method called |
| Interactive happy path (new dir, confirmed) | `confirm_create_directory` returns True; `show_creating_directory` called |
| Interactive abort | `show_cancellation` called; no table methods called |
| CLI happy path (existing dir) | `show_header` called; export table methods called |
| CLI non-directory path | `show_not_a_directory_error` called; no table methods called |
| CLI missing dir, no `--create` | `show_directory_not_found_error` called; no table methods called |
| CLI missing dir, `create=True` | `show_creating_directory` called; export proceeds |

---

## Quality Gates

All three must pass cleanly before the phase is considered complete:

```
just lint       # ruff — no new errors
just typecheck  # mypy — no new errors
just test       # pytest — all tests pass
```

---

## Manual Validation

### Import — interactive mode

```
uv run nwtrack import tables-csv
```

1. Header rule is displayed: `Import Tables from CSV`
2. Prompt asks for source directory
3. Enter a valid directory containing CSV files — import completes with success message
4. Re-run; enter `q` at the prompt — cancellation message is shown, no import occurs
5. Re-run; enter a directory where import will fail (e.g. missing required CSV) — error message
   is shown

### Import — CLI mode

```
uv run nwtrack import tables-csv --source-dir <path>
```

1. Header rule is displayed
2. Import completes with success message (no prompt shown)
3. Run with an invalid path — error message is shown

### Export — interactive mode

```
uv run nwtrack export tables-csv
```

1. Header rule is displayed: `Export Tables to CSV`
2. Prompt asks for target directory
3. Enter an existing directory — export completes; per-table success or skip messages shown
4. Enter a non-existent directory — confirmation prompt shown; confirm Yes → directory created,
   export proceeds; confirm No → prompt repeats
5. Enter `q` — cancellation message shown, no export occurs

### Export — CLI mode

```
uv run nwtrack export tables-csv --target-dir <existing-path>
uv run nwtrack export tables-csv --target-dir <new-path> --create
uv run nwtrack export tables-csv --target-dir <missing-path>         # expect error
uv run nwtrack export tables-csv --target-dir <file-path>            # expect error
```

Each case should display the correct message and take the correct action.

---

## Regression Check

The following behaviors must be identical before and after the refactor:

- `nwtrack import tables-csv` and `nwtrack import tables-csv --source-dir <path>` produce the
  same output format as before
- `nwtrack export tables-csv` (interactive and CLI) produces the same output format as before
- No other CLI commands are affected
- `just check` passes on the full codebase (not just the changed files)

---

## Definition of Done

- [ ] `ImportTablesCSVPresenter` and `ExportTablesCSVPresenter` Protocols defined in
  `application/ports/presentation.py`
- [ ] `RichImportTablesCSVPresenter` and `RichExportTablesCSVPresenter` implemented in
  `entrypoints/cli/adapters/csv_presenters.py`
- [ ] `import_tables_csv` use case has no direct imports of `rich.console` or `rich.prompt`
- [ ] `export_tables_csv` use case has no direct imports of `rich.console` or `rich.prompt`
- [ ] Both use cases inject presenter via constructor
- [ ] Test files exist and all assertions in the table above are covered
- [ ] `just lint`, `just typecheck`, `just test` all pass
- [ ] Manual walkthrough of import and export (interactive and CLI) confirms identical behavior
