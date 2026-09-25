# Phase 14 Plan: Tag CLI CRUD

## 1. Tag Command Surface

1. Add a `tags` Typer command group.
2. Add interactive `list`, `create`, `update`, and `delete` commands for tags.
3. Keep command wiring consistent with the existing institution command structure.

## 2. Tag List And Shared Admin Helper

1. Add a shared helper that builds tag list rows with linked-account counts.
2. Add any DTO or read-model support needed for tag list output.
3. Implement the tag list use case and Rich list presenter.

## 3. Tag Create And Update Workflows

1. Add a shared tag-name normalization helper used by create and update.
2. Add presentation ports and Rich presenters for tag create and update workflows.
3. Implement create and update use cases with preview, confirmation, duplicate validation, and refreshed-list success output.

## 4. Tag Delete Workflow

1. Add presentation port and Rich presenter for tag deletion.
2. Implement delete use case with ID-based selection and delete preview.
3. Block deletion when any account still references the selected tag, with clear linked-account messaging.

## 5. Validation And Compatibility

1. Add automated tests for tag CLI registration, presenters, and interactive use cases.
2. Add regression checks proving current account, reporting, and CSV workflows remain unchanged in this phase.
3. Run and record the required quality gates for linting, type checking, and tests.
