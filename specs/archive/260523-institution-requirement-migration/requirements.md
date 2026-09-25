# Phase 21 — Institution Requirement Migration Plan: Requirements

## Scope

### What this phase delivers

A new `nwtrack admin` CLI subgroup with two commands:

1. `nwtrack admin list-unassigned` — diagnostic: lists accounts that have no institution assigned, as a Rich table.
2. `nwtrack admin assign-institutions` — remediation: interactive workflow to assign an institution to each unassigned account one at a time.

A written migration strategy section (in this spec) defining the path toward a future phase that enforces institution as mandatory.

No schema changes are required. The `institution_id` FK on `Account` is already nullable. This phase adds only use cases, a presenter protocol, a Rich adapter, and CLI wiring.

### What this phase does not deliver

- Enforcement of institution as required on accounts (deferred to a future phase).
- Bulk assignment (all accounts at once without confirmation per account).
- Any change to the `accounts create` or `accounts update` workflows — those already support optional institution selection.
- New database columns, migrations, or ORM changes.
- Any change to existing reporting or balance commands.

---

## Data shape

No new tables or columns. The relevant existing fields:

| Entity    | Field            | Type       | Note                             |
|-----------|------------------|------------|----------------------------------|
| Account   | `institution_id` | `int\|None` | Already nullable; `None` = unassigned |
| Account   | `institution`    | `Institution\|None` | ORM relationship, loaded via `selectin` |
| Institution | `id`, `name`   | `int`, `str` | Reference data for the selector |

---

## Decisions

### Admin subgroup

Commands are placed under `nwtrack admin` (a new Typer sub-app registered in `app.py`). This signals they are one-time remediation tools, not part of the routine monthly workflow.

### Diagnostic output

`list-unassigned` renders a Rich table with columns: Account ID, Name, Category, Currency, Status. Accounts are sorted by name. An empty-state message is shown when zero accounts lack institutions — this is the goal state.

### Remediation workflow (`assign-institutions`)

Follows the existing interactive use case pattern (show header → list unassigned accounts → loop: select account → select institution → confirm → save → next). The loop continues until the user exits or all accounts are assigned. On exit, a summary shows how many were assigned in the session. If no accounts are unassigned when the command starts, an informational message is shown and the command exits cleanly.

### Institution selection in remediation

Institutions are selected from the existing institution list (same selector pattern as `accounts update`). If no institutions exist, the remediation workflow shows a clear error directing the user to create institutions first.

### Cutover criteria (deferred)

Institution is **not** enforced as required in this phase. The cutover — making `institution_id` non-nullable at the DB level and rejecting account creation without an institution — is deferred to a future phase. The migration strategy defined here is:

1. Use `admin list-unassigned` to identify gaps.
2. Use `admin assign-institutions` to remediate them interactively.
3. Confirm zero unassigned accounts via `admin list-unassigned`.
4. A future phase adds the DB migration to make `institution_id NOT NULL` and updates `accounts create` / `accounts update` validation to require institution selection.

---

## Context

### Patterns to follow

- CLI command module: `entrypoints/cli/commands/admin.py`, registered in `app.py` as `admin_app`.
- Use case class + `main()` structure: mirrors `list_accounts.py` (diagnostic) and `update_account_info.py` (remediation).
- Presenter protocol defined in `application/ports/presentation.py`.
- Rich adapter in `entrypoints/cli/adapters/admin_presenters.py`.
- `FetchService` for read operations; `UnitOfWork` for the institution assignment write.
- DI wiring in `main()` functions follows the same `build_base_container()` + `container.register(...)` chain.

### Tone

Commands are administrative / one-time. Output language should be clear and factual, not alarming. The empty-state on `list-unassigned` should be presented positively ("All accounts have an institution assigned.").
