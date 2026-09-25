# Phase 10 Plan: Institution Schema Foundation

## 1. Institution Persistence Baseline

1. Add the `Institution` entity and ORM mapping with fields `id`, `name`, and optional `description`.
2. Add the `institutions` table to the schema creation path using the project’s existing SQLAlchemy metadata workflow.
3. Preserve the small first-class reference-data shape defined in Phase 9 without adding extra institution attributes.

## 2. Account Schema Integration

1. Add a nullable `institution_id` reference from accounts to institutions.
2. Ensure account persistence continues to support records with no institution assigned.
3. Keep all existing account workflows valid by limiting this phase to schema and persistence support only.

## 3. Repository And Unit Of Work Support

1. Add an `InstitutionsRepository` protocol with the baseline persistence methods required for this phase.
2. Implement the SQLAlchemy repository for institutions.
3. Extend `UnitOfWork` and `SQLAlchemyUnitOfWork` so institution persistence is available as `uow.institutions`.

## 4. Compatibility Boundaries

1. Preserve the existing CSV initialization and export contracts in this phase.
2. Explicitly defer institution CLI CRUD, account workflow integration, reporting changes, and institution-specific fetch methods.
3. Record that delete semantics for referenced institutions remain intentionally undecided until Phase 11.

## 5. Validation

1. Add automated tests that prove institution schema creation, repository behavior, and optional account linkage.
2. Add compatibility tests that prove existing account data still initializes and reads correctly without institutions.
3. Run and record the required quality gates for linting, type checking, and tests.
