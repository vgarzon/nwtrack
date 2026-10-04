---
name: feature-close
description: Close out a finished feature — archive its spec directory, remove the backlog row and item file, add a CHANGELOG entry, push, refresh the PR description, rebase-merge into devel, delete the branch, and prune. Trigger on "close the feature", "archive and merge", "ship it", "finish <slug>", or /feature-close.
---

# Feature Close

Lifecycle: `feature-spec` → `feature-implement` → **`feature-close`**

**Starts from:** an open PR into `devel` from `feature/<slug>` (from `feature-implement`).
**Ends with:** the PR rebase-merged, the spec archived, the backlog row and item file removed,
`CHANGELOG.md` updated, and the feature branch deleted locally and remotely.
**Next:** nothing automatic. Promoting `devel` to `main` is a separate PR the user requests.

Final steps after `feature-implement` (PR open, validation done). Merge is outward-facing, so
this runs only when the user invokes it; invoking it authorizes the push, merge and branch
deletion for that one PR and nothing else.

## Workflow

### 1. Preflight

- Identify the feature slug and its PR (`gh pr view`). Be on the `feature/<slug>` branch with a
  clean working tree.
- Check the PR is mergeable and its checks are not failing (`gh pr view --json
  mergeable,statusCheckRollup`, `gh pr checks`). Stop and report if not.
- Check `validation.md`'s definition of done is met. If anything is open, stop and tell the user
  rather than merging.
- Run the full `just check` if anything changed since the last full run (follow-up tweaks often
  only ran affected tests); report real results.

### 2. Housekeeping commit

Skip any item that is already done (verify it first) — e.g. the archive may have been committed
during implementation. Only commit what is actually missing.

1. Move `specs/YYMMDD-<slug>/` to `specs/archive/<slug>/` with `git mv`.
2. Delete `specs/backlog/<slug>.md` and remove its row from `specs/backlog.md`.
3. Add a one-line entry at the top of `CHANGELOG.md`, matching the existing style; call out any
   behavior change in bold as earlier entries do.
4. Confirm `README.md`/`CLAUDE.md`/`specs/tech-stack.md` reflect the shipped behavior.
5. Commit: `docs: archive <slug> spec, update backlog and changelog`, with the attribution
   trailer.

### 3. Push and refresh the PR

Push the branch. Rewrite the PR body with `gh pr edit --body-file` so it describes the final
shipped state (not stale intermediate decisions), ending with the attribution line.

### 4. Merge

```
gh pr merge <number> --rebase --delete-branch
git checkout devel
git pull --ff-only
git fetch --prune
```

Never merge into `main`; promoting `devel` to `main` is a separate PR the user requests.

### 5. Report

State: PR merged and its rebased HEAD, branches deleted/pruned, remaining local branches, and
anything not re-verified. Do not touch unrelated stale branches.

## Constraints

- Do not merge with failing checks or an unmet definition of done.
- Rebase strategy only, with `--delete-branch`.
- For bug fixes use the `bug-fix` skill's Close action instead.
