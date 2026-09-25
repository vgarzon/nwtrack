# Phase 13 Plan: Tag Schema Foundation

## 1. Tag Persistence Baseline

1. Add the `Tag` entity and ORM mapping with fields `id`, `name`, and optional `description`.
2. Add the `tags` table to the schema creation path using the project’s existing SQLAlchemy metadata workflow.
3. Preserve the small first-class reference-data shape defined in Phase 9 without adding extra tag attributes.

## 2. Account-Tag Association Integration

1. Add the `account_tags` association table with foreign keys to accounts and tags.
2. Enforce uniqueness of `(account_id, tag_id)` so one account cannot hold the same tag twice.
3. Use database-level cascading cleanup on association rows when an account or tag is deleted.
4. Keep all existing account workflows valid by limiting this phase to schema and persistence support only.

## 3. Repository And Unit Of Work Support

1. Add a `TagsRepository` protocol with the baseline persistence and association methods required for this phase.
2. Implement the SQLAlchemy repository for tags, including account-tag read and replacement helpers.
3. Extend `UnitOfWork` and `SQLAlchemyUnitOfWork` so tag persistence is available as `uow.tags`.
4. Add ORM relationship support needed for future account and reporting phases without changing current CLI flows.

## 4. Compatibility Boundaries

1. Preserve the existing CSV initialization and export contracts in this phase.
2. Ensure existing SQLite databases gain missing tag tables without any inferred or bulk-applied tag assignments.
3. Explicitly defer tag CLI CRUD, account workflow integration, fetch-service changes, reporting changes, and multi-tag aggregation semantics.

## 5. Validation

1. Add automated tests that prove tag schema creation, repository behavior, many-to-many association behavior, and optional account tagging.
2. Add compatibility tests that prove legacy SQLite databases upgrade cleanly and current CSV flows still work without tag CSV files.
3. Run and record the required quality gates for linting, type checking, and tests.
