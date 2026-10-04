# Validation: Demo Sample Data Command

## Automated

Quality gates (all must pass): `just lint`, `just typecheck`, `just test` (or `just check`).

Required assertions:

- Dataset function returns 2 currencies, >= 2 institutions, >= 2 tags, 6-8 accounts, and
  12 consecutive months of balances ending at the reference month.
- Both asset and liability categories are present; every account has an institution; at least
  one account is inactive with matching status history; at least one account is tagged.
- Running the use case against `tmp_path / "demo.db"`:
  - creates the file with the schema stamped at Alembic `head`;
  - loads data readable via repositories and `FetchService`;
  - lets the net worth history and aggregation reports run on it without error.
- Existing target path (file, directory) -> failed `OperationResult`, non-zero CLI exit, target
  bytes unchanged.
- Missing parent directory -> failed result, nothing created.
- Injected failure mid-insert -> partial file removed, error reported.
- CLI:
  - omitting `PATH` is a usage error;
  - a successful run never creates, opens, or migrates the configured database (assert the
    isolated configured path does not exist afterwards);
  - output includes the absolute path, a `db_file_path` snippet, and the
    `NWTRACK_DATABASE__DB_FILE_PATH` alternative.
- No new Alembic revision is added (schema untouched).

## Manual

1. `uv run nwtrack admin create-sample-db /tmp/nwtrack-demo.db` succeeds and prints activation
   guidance.
2. Re-run the same command: refuses with a clear error, file unchanged.
3. With a real configured database in place, confirm its modification time and contents are
   unchanged after the command; with no configured database, confirm none is created.
4. `NWTRACK_DATABASE__DB_FILE_PATH=/tmp/nwtrack-demo.db uv run nwtrack accounts list` and
   `... reports networth-history` show the sample data.
5. Launch the TUI against the sample database: home screen loads, reports render, no startup
   forward-fill prompt appears (data ends at the current month).
6. Follow the printed `config.toml` snippet and confirm `nwtrack config show` reports the new
   path with source `file`.
7. Path in a non-existent directory and an unwritable directory both give clear errors.

## Tone check

Presenter output is concise, states what was and was not changed, and uses the same style as
the other admin presenters.

## Definition of done

- All automated checks above pass and the quality gates are green.
- Manual steps 1-7 verified.
- README, CLAUDE.md, and CHANGELOG updated.
- Backlog item archived per the end-of-feature checklist (row removed, item file deleted, spec
  moved to `specs/archive/demo-sample-data-command/`).
