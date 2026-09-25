# Phase 30 Validation: TUI Account and Administrative Screens

## Automated Tests

### Quality gates (must pass before merge)

```bash
just check   # ruff + mypy + pytest
```

### Feature-specific test assertions

**ConfirmModal**
- Dismisses with `True` when confirmed
- Dismisses with `False` or `None` when cancelled (Escape)

**Institution screens**
- `InstitutionsListScreen` renders a row for each institution in the database
- `InstitutionFormModal` create mode: dismisses with a new `Institution` on valid input; does not dismiss on empty name
- `InstitutionFormModal` edit mode: dismisses with updated `Institution`; pre-populates name and description
- Delete flow: `ConfirmModal` message includes linked account count; confirmed delete removes institution from database

**Tag screens**
- `TagsListScreen` renders a row for each tag
- `TagFormModal` create/edit: same assertions as institution form
- Delete flow: linked account count appears in confirmation message; confirmed delete removes tag and its account associations

**Category screens**
- `CategoriesListScreen` renders a row per category with name and side
- `CategoryFormModal`: dismisses with new `Category` on valid input; side field required

**Account screens**
- `AccountsListScreen` shows both active and inactive accounts (not filtered)
- Create: account appears in list after modal confirms; tags are persisted via `replace_for_account`
- Edit: changed fields (including status and tags) are reflected in the list after dismiss
- Delete: account and its balance records are removed; account no longer appears in list
- `HomeScreen` routes "Accounts" → `AccountsListScreen` (not `StubScreen`)
- `HomeScreen` routes "Admin" → `AdminMenuScreen` (not `StubScreen`)

---

## Manual Validation Steps

### Institution CRUD

1. Launch `nwtrack tui launch`
2. Navigate Home → Admin → Institutions
3. Press `c` → create modal opens; submit empty name → error label shown, modal stays open
4. Enter a name and description → confirm → institution appears in list
5. Navigate to the new row, press Enter → edit modal opens pre-populated; change description → confirm → list updates
6. Press `d` on the row → confirmation modal appears with institution name; press Escape → institution not deleted; press `d` again → confirm → institution removed from list
7. Create an institution, assign it to an account (via CLI or Account screen), then return to institution list and delete → confirmation modal warns about the linked account

### Tag CRUD

1. Navigate Home → Admin → Tags
2. Create, edit, and delete a tag using the same steps as above
3. Assign the tag to an account via Account screen; return to Tags; verify delete confirmation warns about linked account count

### Category create

1. Navigate Home → Admin → Categories
2. Press `c` → modal opens with name and side fields
3. Submit empty name → error shown
4. Enter name + select side → confirm → category appears in list

### Account CRUD

1. Navigate Home → Accounts
2. Verify both active and inactive accounts appear (check status column)
3. Press `c` → create modal; fill all fields including tags; confirm → account appears in list
4. Select the new account, press Enter → edit modal opens pre-populated; change name and add a tag → confirm → list reflects changes
5. Press `d` on the account → confirmation warns about balance deletion; confirm → account and balances removed
6. Verify that an account with balances: after delete, `nwtrack balances update` CLI no longer shows that account

### Navigation

1. Escape from AccountsListScreen → returns to HomeScreen
2. Escape from AdminMenuScreen → returns to HomeScreen
3. Escape from any institution/tag/category list → returns to AdminMenuScreen
4. Escape from any modal → cancels and returns to the list screen

---

## Error and Edge Cases

| Scenario                                     | Expected behaviour                                          |
|----------------------------------------------|-------------------------------------------------------------|
| Create institution with duplicate name       | Error label shown in modal; not dismissed                   |
| Create tag with duplicate name               | Error label shown in modal; not dismissed                   |
| Create account with duplicate name           | Error label shown in modal; not dismissed                   |
| Delete institution linked to accounts        | Confirmation warns about count; institution `id` set to NULL on linked accounts after delete |
| Delete tag linked to accounts                | Confirmation warns about count; associations removed        |
| Delete account with balance records          | Confirmation warns; balances deleted before account         |
| Create category with no categories present   | Create modal is the only option; no edit/delete offered     |
| Open account edit with no institutions       | Institution field shows empty/none option but does not error |
| Open account edit with no tags               | Tag SelectionList shows empty; save works without tags      |

---

## Definition of Done

- [x] `just check` passes (ruff, mypy, pytest) — 311 tests pass
- [x] All feature-specific test assertions above pass
- [ ] Manual walkthrough completed for institution, tag, category, and account CRUD
- [x] Navigation: HomeScreen no longer routes "Accounts" or "Admin" to `StubScreen`
- [x] Delete operations with linked entities display correct warning counts
- [x] Account list shows all accounts regardless of status (`active_only=False` asserted in tests)
- [x] Spec files committed alongside implementation
