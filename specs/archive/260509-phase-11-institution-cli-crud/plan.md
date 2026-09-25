# Phase 11 Plan: Institution CLI CRUD

## 1. Institution CLI Surface

1. Add an `institutions` Typer command group.
2. Add interactive `list`, `create`, `update`, and `delete` commands for institutions.
3. Keep command wiring consistent with the existing category and account command structure.

## 2. Presenter And UI Support

1. Add presentation ports for institution list, create, update, and delete workflows.
2. Add Rich presenter adapters for those workflows.
3. Add any institution-specific table, preview, and prompt helpers needed for readable CLI interaction.

## 3. Use Cases And Repository Extensions

1. Add institution use cases for list, create, update, and delete.
2. Extend institution repository support for update, delete, and linked-account counting.
3. Keep institution reads inside the institution use cases instead of adding FetchService methods in this phase.

## 4. Delete Safety And Validation

1. Enforce case-insensitive duplicate-name validation for create and update.
2. Enforce ID-based institution selection for update and delete.
3. Block deletion when any account still references the institution, with clear linked-account messaging.

## 5. Validation

1. Add automated tests for institution CLI workflows, repository behavior, and delete restrictions.
2. Add manual checks for empty-state handling, cancellation flows, ID-based selection, and usage-count visibility.
3. Run and record the required quality gates for linting, type checking, and tests.
