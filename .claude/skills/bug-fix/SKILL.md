---
name: bug-fix
description: Capture, triage, fix and close nwtrack bugs using specs/bugs.md and specs/bugs/ — report a bug, list bugs, confirm with a failing test, fix on a fix/<slug> branch, open the PR, and close out. Trigger on "report a bug", "log a bug", "list bugs", "fix bug X", "triage", "close bug", or /bug-fix.
---

# Bug Fix

Lifecycle: **Report** → **Triage** → **Fix** → **Close** (all actions of this one skill; each
can be invoked on its own, in separate sessions).

**Starts from:** a symptom the user describes. **Ends with:** a merged `fix/<slug>` PR and the bug
removed from the board. Nothing is merged except in **Close**, which runs only on request.

Manages `specs/bugs.md` (the board) and `specs/bugs/<slug>.md` (one file per bug). Bugs are kept
separate from `specs/backlog.md`. Lighter than `feature-spec`: small bugs get no spec directory.

## Tiers (decide at triage)

- **Small** — local cause, obvious fix, no schema change, no new UX decision. Bug file + PR only.
- **Large** — needs a migration, a design decision, or touches several layers. Add it to
  `specs/backlog.md` as a `ready` item (via the `backlog` skill), delete the bug file and its row,
  and continue with `feature-spec`.

## Actions

### Report

1. Derive a kebab-case `slug`.
2. Write `specs/bugs/<slug>.md`:
   ```markdown
   ---
   name: <slug>
   status: reported
   severity: <critical|major|minor>
   ---

   ## Symptom

   ## Repro steps

   ## Expected vs actual

   ## Version / environment

   ## Suspected area

   ## Diagnosis
   <root cause and evidence, filled in during Triage/Fix>
   ```
3. Add a row to `specs/bugs.md` (status, severity, link, one-liner).
4. Capture only what the user said — no interview, no invented repro steps. Propose a severity
   if the user did not give one.

### List

Read `specs/bugs.md` and summarize, ordered by severity (critical first).

### Triage / confirm

1. Reproduce. Write a **failing test** in the matching `tests/` directory and confirm it fails
   for the right reason (or record a precise repro command).
2. Record the root cause in the bug file's Diagnosis section as soon as it is known — a
   diagnosis-only session is a valid stopping point; it ends at `confirmed` with no code changed.
   Set status `confirmed` in the bug file and the board.
3. **Clarify only when blocked.** Report stays interview-free; Triage may ask the user, with
   `AskUserQuestion` (at most 3 targeted questions in one call), in two cases only:
   - *Cannot reproduce after a real attempt.* Ask only for what the report lacks — exact command
     or screen, nwtrack version, where the data came from (CSV import, sample data, hand entry),
     error text or log excerpt. Never ask what the code, logs or a quick experiment can answer.
     If the answers still don't yield a repro, set `cannot-reproduce` and note what was tried.
   - *Tier is ambiguous* (e.g. the fix looks like it needs a migration or a design decision).
     Recommend a tier and let the user decide whether to escalate to the backlog.
4. Choose the tier. For `wontfix`, record the reason and ask whether to keep or delete the file.

### Fix (small tier)

1. `git checkout devel && git checkout -b fix/<slug>`; set status `in-progress` (file + board).
2. Find the root cause; make the minimal fix. If it grows, escalate to the large tier.
3. Regression test must pass; run `just check` (ruff, mypy, full pytest).
4. Commit as `fix(<scope>): <summary>` with the repo's attribution trailer.
5. Push and open a PR **into `devel`** with this body:
   - **Symptom**
   - **Root cause**
   - **Fix**
   - **Regression test**
   - **Risk / blast radius**
   - **Data impact** — do existing databases need repair? If so the repair must be an Alembic
     migration, which makes this a large-tier bug.
6. Hotfixes are not special: critical bugs still go through `devel`, then a fast-tracked
   `devel` → `main` promotion PR.

### Close

Runs only when the user asks. Invoking it authorizes the push, merge and branch deletion for
that one PR. Bookkeeping goes **on the fix branch before the merge**, so the PR carries it and
nothing is committed to `devel` directly.

1. Preflight: on `fix/<slug>` with a clean tree; the PR is mergeable and its checks are not
   failing (`gh pr view --json mergeable,statusCheckRollup`; no checks at all is fine); the full
   `just check` has run since the last change. Stop and report otherwise.
2. Bookkeeping commit (skip what is already done): remove the row from `specs/bugs.md`, delete
   `specs/bugs/<slug>.md`, and if user-visible add a `Fixed:` line to the top of `CHANGELOG.md`.
   Commit as `docs: close <slug> bug`.
3. Push and refresh the PR description so it matches the final fix.
4. Merge: `gh pr merge <number> --rebase --delete-branch`, then `git checkout devel`,
   `git pull --ff-only`, `git fetch --prune`.
5. Report the merged HEAD, branches pruned, and anything not re-verified.

No archive directory for small bugs; the PR description is the permanent record.

## Constraints

- Never fix before a failing test or precise repro exists (unless it is genuinely untestable —
  say so in the PR).
- Never merge into `main` directly.
- Don't create `specs/YYMMDD-<slug>/` from this skill.
