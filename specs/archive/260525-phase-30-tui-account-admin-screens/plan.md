# Phase 30 Plan: TUI Account and Administrative Screens

## Task Groups

### 1. FetchService Additions ✓

1.1 ✓ Verified `FetchService.get_accounts(active_only=False)` returns all accounts  
1.2 ✓ Added `FetchService.get_tags_for_account(account_id: int) -> list[Tag]`  
1.3 ✓ `FetchService.get_all_currencies()` already existed; confirmed return type `list[Currency]`

---

### 2. Shared Confirm Modal ✓

2.1 Implement `ConfirmModal(ModalScreen[bool])` in `entrypoints/tui/screens/confirm_modal.py`  
  - Constructor: `message: str`, `confirm_label: str = "Confirm"`, `cancel_label: str = "Cancel"`
  - Centered overlay with message, two buttons (or Enter/Escape bindings)
  - Returns `True` on confirm, `False`/`None` on cancel  
2.2 Write unit test for `ConfirmModal` dismiss behaviour

---

### 3. Admin Sub-Menu Screen ✓

3.1 Implement `AdminMenuScreen(Screen)` in `entrypoints/tui/screens/admin_menu.py`  
  - Follows `ReportsMenuScreen` pattern exactly
  - Menu items: "Institutions", "Tags", "Categories"
  - Escape returns to home  
3.2 Wire `HomeScreen.on_list_view_selected` "Admin" branch to push `AdminMenuScreen` instead of `StubScreen`

---

### 4. Institution Screens ✓

4.1 Implement `InstitutionFormModal(ModalScreen[Institution | None])`  
  - Fields: name (required), description (optional)
  - Create mode: empty fields; Edit mode: pre-populated fields
  - Inline validation: name required, shows error label on empty submit  
4.2 Implement `InstitutionsListScreen(Screen)`  
  - `DataTable` with columns: ID, Name, Description, Linked Accounts
  - Bindings: `c` = create, `Enter` = edit selected row, `d` = delete selected row  
  - On create modal dismiss: insert via `uow.institutions.insert()`, refresh table  
  - On edit modal dismiss: update via `uow.institutions.update()`, refresh table  
  - On delete: push `ConfirmModal` with linked-account warning; on confirm, `uow.institutions.delete_by_id()`; refresh table  
4.3 Wire `AdminMenuScreen` "Institutions" branch to push `InstitutionsListScreen`

---

### 5. Tag Screens ✓

5.1 Implement `TagFormModal(ModalScreen[Tag | None])`  
  - Fields: name (required), description (optional)
  - Same validation pattern as `InstitutionFormModal`  
5.2 Implement `TagsListScreen(Screen)`  
  - `DataTable` with columns: ID, Name, Description, Linked Accounts  
  - Bindings: `c` = create, `Enter` = edit, `d` = delete  
  - Delete warns on linked account count before confirming  
5.3 Wire `AdminMenuScreen` "Tags" branch to push `TagsListScreen`

---

### 6. Category Screens ✓

6.1 Implement `CategoryFormModal(ModalScreen[Category | None])`  
  - Fields: name (required), side (required; select asset / liability)  
  - Validation: name required, side required  
6.2 Implement `CategoriesListScreen(Screen)`  
  - `DataTable` with columns: Name, Side  
  - Binding: `c` = create only (no edit or delete in this phase — see requirements)  
  - On create modal dismiss: insert via `uow.categories.insert()`, refresh table  
6.3 Wire `AdminMenuScreen` "Categories" branch to push `CategoriesListScreen`

---

### 7. Account Form Modal ✓

7.1 Implement `AccountFormModal(ModalScreen[dict | None])`  
  - Returns a dict with updated field values (or `None` on cancel)  
  - Fields: name (Input), description (Input), category (Select from categories), institution (Select; optional), currency (Select), status (Select; edit mode only), tags (SelectionList multi-select)  
  - Create mode: status field hidden; defaults: currency=USD, status=active  
  - Edit mode: all fields pre-populated including current tags  
  - Inline validation: name required  
7.2 Consider breaking into sub-sections if modal becomes complex (e.g. scrollable `Vertical` container)

---

### 8. Account List Screen ✓

8.1 Implement `AccountsListScreen(Screen)`  
  - `DataTable` with columns: ID, Name, Status, Category, Side, Institution, Currency, Tags  
  - Shows all accounts (active + inactive)  
  - Bindings: `c` = create, `Enter` = edit selected, `d` = delete selected  
  - On create: collect form data, call `uow.accounts.insert()` and `uow.tags.replace_for_account()`, refresh  
  - On edit: load account + tags, open `AccountFormModal` pre-populated, apply changes, refresh  
  - On delete: push `ConfirmModal` warning that balances will also be deleted; on confirm, call `uow.balances.delete_by_account_id()` then `uow.accounts.delete_by_id()`  
8.2 Wire `HomeScreen.on_list_view_selected` "Accounts" branch to push `AccountsListScreen` instead of `StubScreen`

---

### 9. Tests ✓

9.1 Tests for `ConfirmModal`: verify `True`/`False` return values  
9.2 Tests for institution CRUD: list, create, edit, delete (including linked-account guard message)  
9.3 Tests for tag CRUD: list, create, edit, delete  
9.4 Tests for category list and create  
9.5 Tests for account list: verifies all accounts shown (active + inactive)  
9.6 Tests for account create: verifies account inserted with correct fields and tags  
9.7 Tests for account edit: verifies updated fields and tag replacement  
9.8 Tests for account delete: verifies account and its balances are removed  
9.9 Confirm `HomeScreen` routes "Accounts" and "Admin" to correct screens (not `StubScreen`)

---

## Recommended Implementation Order

Groups 1–3 are foundations; Groups 4–6 are independent once Group 3 is done; Group 7–8 depend on Group 1; Group 9 follows each group.
