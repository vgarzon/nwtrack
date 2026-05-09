# Phase 12b Plan: Interactive Balance Creation

## 1. Command And Presenter Surface

1. Add a `balances create` command to the existing balance CLI group.
2. Add presenter support for the create workflow header, active-account display, account selection, preview, confirmation, success, and duplicate validation messaging.
3. Reuse existing balance and account display patterns where practical without changing the surrounding balance commands.

## 2. Create Workflow Integration

1. Implement a balance-create use case that shows active accounts and collects account ID, month, and amount.
2. Validate account eligibility against active accounts only for this phase.
3. Insert exactly one balance row after confirmation and show the created-balance preview on success.

## 3. Duplicate And Cancellation Handling

1. Detect existing `(account_id, month)` balance rows before insert.
2. Reject duplicates clearly and direct the user to `balances update`.
3. Ensure cancellation paths exit cleanly without modifying persisted data.

## 4. Validation

1. Add automated tests for successful create, duplicate rejection, cancellation, and empty-eligible-account behavior.
2. Add manual checks for account selection, month entry, preview/confirmation, and success output.
3. Run and record the required quality gates for linting, type checking, and tests.
