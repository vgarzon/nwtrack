# Phase 9 Validation: Spec And Domain Shape Alignment

## Task Group Checklist

Update this checklist as task groups in `plan.md` are completed.

- [X] Shared Terminology
- [X] Institution Spec Baseline
- [X] Tag Spec Baseline
- [ ] Reporting Boundary Alignment
- [ ] Follow-On Phase Readiness

## Automated

- `uv run ruff check .` passes
- `uv run mypy .` passes
- `uv run pytest` passes

Specific assertions for this phase:

- The spec directory `specs/260508-spec-and-domain-shape-alignment/` exists with `requirements.md`, `plan.md`, and `validation.md`.
- The requirements document defines baseline field shapes for `Institution` and `Tag`.
- The requirements document states that institutions are initially optional on accounts.
- The requirements document states that institution names are unique and that institutions remain first-class reference data.
- The requirements document states that existing accounts are preserved without forced institution reassignment.
- The requirements document states that tags support zero-to-many account associations.
- The requirements document states that tag names are unique and that tags remain first-class reusable reference data.
- The requirements document states that existing accounts are preserved without forced tag assignment.
- The requirements document defines reporting vocabulary but defers full aggregated reporting behavior to later phases.
- The requirements document states that later feature phases must include explicit testing and quality-check requirements.

## Manual

1. Read `requirements.md` and confirm the phase is documentation-only, not an implementation spec for schema or CLI behavior.
2. Confirm the institution section defines `Institution` as first-class reference data with baseline fields `id`, `name`, and optional `description`.
3. Confirm the institution baseline keeps account-to-institution assignment optional and preserves accounts without forced reassignment.
4. Confirm the tag section defines `Tag` as first-class reusable reference data with baseline fields `id`, `name`, and optional `description`.
5. Confirm the tag baseline keeps account-to-tag assignment optional and preserves accounts without forced tag assignment.
6. Confirm the reporting section establishes shared terminology without locking in future CLI design too early.
7. Confirm the scope and deferred decisions leave later phases room to define implementation details independently.
8. Confirm the spec requires future phases to define concrete testing coverage and quality checks as part of validation.

## Tone Check

- Terminology is consistent with the CLI-first, local-first mission.
- The spec uses precise language and avoids product promises that belong to later phases.
- Compatibility expectations are stated carefully rather than overcommitted.
- Testing expectations are described as required feature work, not optional follow-up.

## Definition Of Done

- The Phase 9 spec directory exists with the three required documents.
- The spec captures the user-provided scope, deferrals, and migration context.
- The spec aligns with `specs/mission.md`, `specs/tech-stack.md`, and `specs/roadmap.md`.
- Later implementation phases can proceed without reopening baseline terminology questions.
- Later feature specs are expected to include explicit testing and quality-check steps in both requirements and validation.
