# Phase 24 Validation: CSV Presenter Protocol Migration

## Automated Tests

### Test files

- `tests/use_cases/test_import_tables_csv.py` — 11 tests
- `tests/use_cases/test_export_tables_csv.py` — 11 tests

### Presenter interaction assertions — import

| Test | Result |
|---|---|
| Interactive happy path — `show_header` called | PASS |
| Interactive happy path — `prompt_for_source_dir` called | PASS |
| Interactive happy path — `show_import_success` called with source dir | PASS |
| Interactive abort (`q`) — `show_cancellation` called; no success | PASS |
| CLI happy path — `show_header` and `show_import_success` called | PASS |
| Service exception — `show_error` called; no success | PASS |

### Presenter interaction assertions — export

| Test | Result |
|---|---|
| Interactive happy path — `show_header` called; table methods called | PASS |
| Interactive abort (`q`) — `show_cancellation` called; no table methods | PASS |
| Interactive confirm-create — `confirm_create_directory` → `show_creating_directory` | PASS |
| CLI happy path — `show_header` called; export methods called | PASS |
| CLI non-directory path — `show_not_a_directory_error` called | PASS |
| CLI missing dir, no `--create` — `show_directory_not_found_error` called | PASS |
| CLI missing dir, `create=True` — `show_creating_directory` called; export proceeds | PASS |

---

## Quality Gates

All three passed cleanly:

```
just lint       ✓  0 errors
just typecheck  ✓  0 errors
just test       ✓  248 passed
```

---

## Regression Verification

Confirmed after implementation:

- `import_tables_csv.py` and `export_tables_csv.py` contain zero direct imports of
  `rich.console` or `rich.prompt`
- All 248 tests (full suite) pass — no regressions in other use cases
- CLI command files (`imports.py`, `export.py`) contain no direct `Console` resolution;
  mode-announcement prints removed (minor UX improvement, allowed per spec)

---

## Definition of Done

- [x] `ImportTablesCSVPresenter` and `ExportTablesCSVPresenter` Protocols defined in
  `application/ports/presentation.py`
- [x] `RichImportTablesCSVPresenter` and `RichExportTablesCSVPresenter` implemented in
  `entrypoints/cli/adapters/csv_presenters.py`
- [x] `import_tables_csv` use case has no direct imports of `rich.console` or `rich.prompt`
- [x] `export_tables_csv` use case has no direct imports of `rich.console` or `rich.prompt`
- [x] Both use cases inject presenter via constructor
- [x] Test files updated; all presenter interaction assertions covered
- [x] `just lint`, `just typecheck`, `just test` all pass
