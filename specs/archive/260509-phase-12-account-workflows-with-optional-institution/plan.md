# Phase 12 Plan: Account Workflows With Optional Institution

## 1. Account Input And Presenter Updates

1. Extend account creation and update workflow inputs to carry optional institution selection as the first editable field.
2. Add institution selection and institution display support to the account presenters.
3. Use direct institution indexes with `0` for no institution and `q` for quit.

## 2. Minimal Fetch And Read Support

1. Extend account-facing fetch support only as needed to retrieve institutions for presenter selection.
2. Keep institution-aware reads limited to account workflow needs in this phase.
3. Preserve existing account read behavior for accounts that have no institution assigned.

## 3. Account Use Case Integration

1. Thread optional `institution_id` through `accounts create`.
2. Thread optional `institution_id` through `accounts update`, including reassignment and clearing.
3. Ensure create and update previews and success flows show institution consistently.

## 4. Account List Output

1. Add institution display to the account list table.
2. Place the institution column immediately after `ID`.
3. Render unassigned institutions as blank cells in account tables only.
4. Keep active-only behavior and the rest of the account list flow unchanged.

## 5. Validation

1. Add automated tests for create, update, and list behavior with assigned and unassigned institutions.
2. Add manual checks for indexed selection, empty-institution handling, reassignment, and clearing behavior.
3. Run and record the required quality gates for linting, type checking, and tests.
