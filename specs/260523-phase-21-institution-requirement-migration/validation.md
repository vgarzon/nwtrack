# Phase 21 — Institution Requirement Migration Plan: Validation

## Automated Checks

### Quality gates (must all pass before phase is complete)

```
just check   # runs: ruff lint → mypy → pytest
```

Or individually:
```
just lint
just typecheck
just test
```

### Feature-specific test assertions

**`test_admin_list_unassigned.py`**
- `ListUnassignedAccounts.run()` calls `presenter.show_empty_state()` when no accounts have `institution_id = None`.
- `ListUnassignedAccounts.run()` calls `presenter.display_unassigned(accounts)` with exactly the accounts missing an institution when some exist.
- The result returned is `OperationResult(success=True)` in both cases.
- Accounts with an institution assigned do not appear in `display_unassigned`.
- `get_without_institution` repo query returns results sorted by `account.name`.

**`test_admin_assign_institutions.py`**
- When no institutions exist, `presenter.show_no_institutions_error()` is called and the use case exits with `success=False`.
- When no unassigned accounts exist at entry, `presenter.show_empty_state()` is called and the loop does not start.
- Successful assignment: account's `institution_id` in the DB equals the selected institution's `id` after `run()` completes.
- `presenter.show_assignment_success()` is called once per confirmed assignment.
- `presenter.show_session_summary(assigned_count)` is called on exit with the correct count.
- Cancellation mid-loop: previously assigned accounts in the same session are persisted; summary reflects actual count.
- Declined confirmation: no DB write; assignment count stays 0.

---

## Manual Walkthrough

### Prerequisite state

Use a local database that has at least:
- Two or more institutions
- At least two accounts: one with an institution assigned, one without

### Diagnostic command

```
uv run nwtrack admin list-unassigned
```

- Output is a Rich table showing only the account(s) with no institution.
- The account that already has an institution assigned does not appear.
- Assign the institution to all unassigned accounts (via `assign-institutions` or `accounts update`), then run `list-unassigned` again.
- Output should show: "All accounts have an institution assigned."

### Remediation command

```
uv run nwtrack admin assign-institutions
```

- Header is shown.
- Unassigned accounts are listed.
- User is prompted to select an account.
- User is prompted to select an institution from the existing list.
- A confirmation prompt shows the proposed assignment.
- On confirm, success message is shown.
- Loop continues — user selects next account or exits with `0`.
- On exit, session summary shows how many were assigned.

### Edge cases to verify manually

- Run `assign-institutions` when zero accounts lack an institution → informational empty-state, command exits cleanly.
- Run `assign-institutions` when zero institutions exist → clear error message directing user to create institutions first.
- Cancel at the account selection prompt → loop exits; any prior assignments in the session are already saved.
- Re-run `list-unassigned` after completing remediation → empty state confirmed.

---

## Definition of Done

- [x] `ruff check src/ tests/` passes with no errors.
- [x] `mypy src/ tests/` passes with no errors.
- [x] `pytest` passes with all new tests green and no regressions (237 total).
- [x] `nwtrack admin list-unassigned` renders a correct Rich table (manual).
- [x] `nwtrack admin assign-institutions` completes the interactive remediation loop (manual).
- [x] Both commands appear under `nwtrack admin --help`.
- [x] `nwtrack --help` shows the `admin` subgroup.
- [x] The written migration strategy (in `requirements.md`) is present, defining the deferred cutover criteria for a future enforcement phase.
