# Phase 21 — Institution Requirement Migration Plan: Implementation Plan

## Status: Complete

All task groups implemented and validated. See validation.md for done checklist.

---

## Task Groups

---

### Group 1 — Application layer: FetchService extension ✅

**Goal:** Add a method to `FetchService` (or inline in the use case) to retrieve accounts where `institution_id IS NULL`.

1.1. ✅ Added `get_accounts_without_institution() -> list[Account]` to `FetchService` (`application/services/fetch.py`).
    - Delegates to `AccountRepository.get_without_institution()`.

1.2. ✅ Added `get_without_institution() -> list[Account]` to `AccountsRepository` protocol (`application/ports/repos.py`) and `SQLAlchemyAccountRepository` (`infra/persistence/repositories/accounts.py`).
    - Query: `select(Account).where(Account.institution_id == None).order_by(Account.name)`.

---

### Group 2 — Application layer: use cases ✅

2.1. ✅ Created `application/use_cases/admin_list_unassigned.py`.
    - `ListUnassignedAccounts(fetcher, presenter)`.
    - `run()`: fetches unassigned accounts, calls `display_unassigned` or `show_empty_state`.
    - `main()`: DI container wired and executed.

2.2. ✅ Created `application/use_cases/admin_assign_institutions.py`.
    - `AssignInstitutions(uow, fetcher, presenter)`.
    - `run()`: guards for no institutions, loops until user exits or all assigned.
    - Each assignment is persisted atomically per account via `uow.accounts.update`.
    - `main()`: DI container wired and executed.

---

### Group 3 — Presentation layer: protocol and Rich adapter ✅

3.1. ✅ Added `AdminListUnassignedPresenter` protocol to `application/ports/presentation.py`.

3.2. ✅ Added `AdminAssignInstitutionsPresenter` protocol to `application/ports/presentation.py`.

3.3. ✅ Created `entrypoints/cli/adapters/admin_presenters.py` with:
    - `RichAdminListUnassignedPresenter` — Rich table with ID, Name, Category, Currency, Status.
    - `RichAdminAssignInstitutionsPresenter` — interactive loop using IntPrompt and Confirm.

---

### Group 4 — CLI wiring ✅

4.1. ✅ Added `admin_app = typer.Typer(...)` to `entrypoints/cli/app.py`; registered as `app.add_typer(admin_app, name="admin")`.

4.2. ✅ Created `entrypoints/cli/commands/admin.py` with:
    - `@admin_app.command("list-unassigned")` → `admin_list_unassigned.main()`.
    - `@admin_app.command("assign-institutions")` → `admin_assign_institutions.main()`.

4.3. ✅ Imported `admin` module in `app.py`'s bottom import block.

---

### Group 5 — Tests ✅

5.1. ✅ Created `tests/use_cases/test_admin_list_unassigned.py`.
    - Tests: no-institution state, empty-state when all assigned, partial filter, name sort order.
    - Verifies `get_without_institution` repo query returns only NULL-institution accounts in name order.

5.2. ✅ Created `tests/use_cases/test_admin_assign_institutions.py`.
    - Tests: no-institutions error, empty-state when all assigned, successful DB write, cancel-persists-prior, declined-confirmation skip.
    - All tests use mock presenter with controlled return sequences.
