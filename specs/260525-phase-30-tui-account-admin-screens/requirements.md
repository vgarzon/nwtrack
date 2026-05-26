# Phase 30 Requirements: TUI Account and Administrative Screens

## Scope

### In Scope

**Accounts section** (accessible from home menu "Accounts"):
- Account list screen showing all accounts (active and inactive) with status, category, institution, and tags
- Account create workflow via modal dialog
- Account edit workflow via modal dialog (name, description, category, institution, currency, status, tags)
- Account delete workflow via confirmation modal

**Admin section** (accessible from home menu "Admin"):
- Admin sub-menu screen with entries: Institutions, Tags, Categories
- Institution list screen, create modal, edit modal, delete confirmation modal
- Tag list screen, create modal, edit modal, delete confirmation modal
- Category list screen and create modal; rename/delete deferred (see below)

### Out of Scope / Deferred

- Category rename and delete: `Category.name` is the primary key; renaming requires delete + recreate with full cascade risk. There are no existing `update_category` or `delete_category` use cases. Category management remains CLI-only for create beyond list+create in this phase.
- Balance operations from account screens (roll-forward, delete, transfer) — covered by Phase 31
- Account status history — covered by Phase 32
- CSV import/export from TUI

---

## Field Reference

### Account fields surfaced in TUI

| Field         | List column | Create | Edit   | Notes                          |
|---------------|-------------|--------|--------|--------------------------------|
| name          | yes         | yes    | yes    | unique                         |
| description   | no          | yes    | yes    |                                |
| category      | yes         | yes    | yes    | select from existing           |
| institution   | yes         | yes    | yes    | optional; select from existing |
| currency      | yes         | yes    | yes    | select from existing           |
| status        | yes         | no     | yes    | active / inactive              |
| tags          | yes         | yes    | yes    | multi-select from existing     |

### Institution fields

| Field       | List | Create | Edit |
|-------------|------|--------|------|
| name        | yes  | yes    | yes  |
| description | no   | yes    | yes  |

### Tag fields

| Field       | List | Create | Edit |
|-------------|------|--------|------|
| name        | yes  | yes    | yes  |
| description | no   | yes    | yes  |

### Category fields

| Field | List | Create |
|-------|------|--------|
| name  | yes  | yes    |
| side  | yes  | yes    |

---

## Decisions

### Modal dialogs for create and edit

Create and edit workflows open as `ModalScreen` overlays, consistent with `BalanceEditModal`. The list screen remains visible in the background. Each modal:
- Returns the created/updated entity (or `None` on cancel) via `dismiss()`
- Validates required fields inline with an error label before dismissing
- Escape cancels without saving

### Delete confirmation modals

Destructive operations use a dedicated confirmation modal pattern:
- Shows entity name and a short warning message (e.g. "Delete institution 'CIBC'? This cannot be undone.")
- For accounts: warns that all balance records will also be deleted
- For institutions with linked accounts: warns how many accounts will lose their institution assignment
- For tags with linked accounts: warns how many account associations will be removed
- Returns `bool` via `dismiss()` — True to confirm, False/None to cancel

### Screen-owned workflow

Screens call `FetchService` and `UnitOfWork` directly from event handlers, following the pattern established in Phase 25. The existing interactive use cases (`AccountCreator`, `UpdateAccountInfo`, etc.) use presenter-driven sequential prompt flows incompatible with TUI event handling. The TUI screens replicate the persistence logic directly rather than driving those use cases.

### Navigation structure

```
HomeScreen
├── Accounts     → AccountsListScreen
│                    [c] Create → AccountFormModal
│                    [Enter] Edit → AccountFormModal
│                    [d] Delete → AccountDeleteConfirmModal
└── Admin        → AdminMenuScreen
    ├── Institutions → InstitutionsListScreen
    │                    [c] Create → InstitutionFormModal
    │                    [Enter] Edit → InstitutionFormModal
    │                    [d] Delete → EntityDeleteConfirmModal
    ├── Tags         → TagsListScreen
    │                    [c] Create → TagFormModal
    │                    [Enter] Edit → TagFormModal
    │                    [d] Delete → EntityDeleteConfirmModal
    └── Categories   → CategoriesListScreen
                         [c] Create → CategoryFormModal
```

Escape from any list screen returns to the previous screen (HomeScreen or AdminMenuScreen).

### Admin as a submenu

"Admin" in the home menu pushes an `AdminMenuScreen` (same pattern as `ReportsMenuScreen`). The sub-menu lists Institutions, Tags, and Categories. This keeps the home menu shallow and mirrors the reports menu pattern.

### Bindings convention

| Key      | Action                    |
|----------|---------------------------|
| `c`      | Open create modal         |
| `Enter`  | Open edit modal (on row)  |
| `d`      | Open delete confirm modal |
| `Escape` | Pop screen / cancel       |

These are screen-level bindings on `DataTable`-based list screens.

### Account list includes all accounts

The account list screen shows all accounts regardless of status (active and inactive), with the status column visible so the user can see which are inactive. This is consistent with Phase 20's direction of not hiding inactive accounts.

---

## Context and Patterns to Follow

- `ModalScreen[T]` pattern from `balance_edit.py` — `DEFAULT_CSS` for centering, `Vertical` container, `Input` fields, inline error label, `dismiss(result)`
- `Screen` + `DataTable` pattern from `balance_update.py` — `on_mount` loads data, `_refresh_table()` clears and repopulates
- `ListView`-based sub-menu pattern from `reports_menu.py`
- `FetchService` provides: `get_accounts()`, `get_all_categories()`, `get_all_institutions()`, `get_all_tags()`, `get_account_by_id()`
- New `FetchService` methods may be needed: `get_all_accounts()` (without `active_only` filter, or using `active_only=False`), `get_tags_for_account(account_id)` — check existing signatures before adding
- Tag multi-select in modals: use a `SelectionList` widget or a `ListView` with checkboxes; Textual's `SelectionList` is the cleaner choice for multi-select
- `HomeScreen` currently pushes `StubScreen` for "Accounts" and "Admin" — replace those stubs with real screens
- All new screen modules go in `entrypoints/tui/screens/`
