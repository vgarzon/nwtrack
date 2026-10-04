---
name: feature-implement
description: Implement a feature from its spec directory (specs/YYMMDD-<slug>/) — commit the spec docs, work through plan.md task groups with a validated commit per group, update plan.md/validation.md, run a final validation, and open a PR into devel. Trigger on "implement the feature spec", "implement <slug>", "start implementation", or /feature-implement.
---

# Feature Implement

Lifecycle: `feature-spec` → **`feature-implement`** → `feature-close`

**Starts from:** the `feature/<slug>` branch with an uncommitted or committed spec directory
(from `feature-spec`), item `in-progress`.
**Ends with:** all task groups committed, validation recorded, and an open PR into `devel`.
**Next:** `feature-close` once the user is satisfied. For bugs use `bug-fix` instead.

Takes a spec produced by the `feature-spec` skill and builds it. Pair with `feature-close` for
the merge and cleanup steps.

## Workflow

### 1. Orient

- Identify the spec directory `specs/YYMMDD-<slug>/` (use the one the user named; otherwise the
  one matching the current `feature/<slug>` branch; otherwise ask).
- Confirm you are on `feature/<slug>`, branched from `devel`. Never implement on `devel`/`main`.
- Read `requirements.md`, `plan.md`, `validation.md`, plus `specs/mission.md` and
  `specs/tech-stack.md`. No new dependencies without user approval.

### 2. Commit the planning docs

Commit the backlog change and the spec directory (and any `specs/backlog*` edits) before any code,
so the branch history starts with the spec.

### 3. Implement task group by task group

For each numbered group in `plan.md`, in order:

1. Implement the group, following the architecture and conventions in `CLAUDE.md` (clean
   architecture layers, use case pattern, presenter ports, tests mirroring `src/`).
2. Validate before committing: `uv run ruff check src/ tests/`, `uv run mypy src/ tests/`, and the
   relevant tests (full `uv run pytest` when shared code changed). Fix failures; never commit red.
3. Mark the group DONE in `plan.md` and add result notes to `validation.md` where relevant.
4. Commit the group on its own: `feat(<scope>): <summary>` (or `test`/`docs`/`refactor` as
   fits), ending with the repo's attribution trailer.

If a group needs a schema change, follow "Adding a schema migration" in `CLAUDE.md`.

### 4. Final validation

After all groups:

1. Run the full gates: `just check` (ruff, mypy, full pytest). Report real output; do not claim
   green without running it.
2. Walk the manual items in `validation.md` that can be exercised (CLI runs, temp databases) and
   record outcomes. State plainly which items were not exercised.
3. Update `plan.md`/`validation.md` to final state and fix any spec/implementation drift in
   `requirements.md`.
4. Update `README.md`, `CLAUDE.md` and the constitution docs (`specs/mission.md`,
   `specs/tech-stack.md`, `specs/backlog.md`) wherever the shipped behavior, commands, stack or
   workflow require it — only what changed, nothing speculative. Do **not** archive the spec or
   edit `CHANGELOG.md` — both belong to `feature-close`.
5. Commit the final docs/spec update.

### 5. Push and open the PR

Push the branch and open a PR **into `devel`** (never `main`) with `gh pr create --base devel`.
Body: summary, behavior/design notes, validation results (with anything not exercised), and
a test plan. End with the attribution line from the session reminder.

## Follow-up changes after the PR is open

Tweaks requested after step 5 (review feedback, tuning, scope adjustments) are handled like a
task group in miniature:

1. Make the change, then run ruff, mypy and the affected tests.
2. Update `plan.md`/`validation.md`/`requirements.md` and any docs if the design or behavior
   drifted (e.g. amounts or wording the spec states).
3. Commit each tweak on its own, push, and keep the PR description current.
4. Run the full `just check` before handing off to `feature-close`; tweak-time runs may have
   covered only the affected tests, so say which was run.

## Constraints

- One validated commit per task group; no squashing across groups.
- Never merge the PR here; stop after it is open and report the URL.
- Don't expand scope beyond the spec; note discoveries in `validation.md` or tell the user.
