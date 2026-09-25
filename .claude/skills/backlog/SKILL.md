---
name: backlog
description: Low-ceremony capture and triage of nwtrack backlog items in specs/backlog.md and specs/backlog/ — add a new idea, list the backlog, promote/demote status, or drop an item. Trigger on "add an idea", "add to the backlog", "list the backlog", "what's in the backlog", "promote X to ready", "drop X from the backlog", or /backlog.
---

# Backlog

Manages `specs/backlog.md` (the board) and `specs/backlog/<slug>.md` (one file per item). This is
intentionally lighter-weight than the `feature-spec` skill — use it for quick capture and
triage, not for writing a full spec.

## Actions

### Add an idea

1. Derive a kebab-case `slug` from the idea.
2. Write `specs/backlog/<slug>.md`:
   ```markdown
   ---
   name: <slug>
   status: idea
   ---

   ## Problem

   <one or two sentences from the user>

   ## Notes

   <anything else the user mentioned>
   ```
3. Add a row to the table in `specs/backlog.md` with status `idea` and a one-line description.
4. Keep it brief — do not interview the user for full scope/decisions/context here; that's what
   the `feature-spec` skill is for once the item is promoted to `ready`.

### List the backlog

Read `specs/backlog.md` and summarize the table back to the user, grouped by status if there are
more than a handful of items.

### Change status (promote/demote/drop)

Update the `status` field in `specs/backlog/<slug>.md`'s frontmatter and the corresponding row in
`specs/backlog.md`'s table. Valid statuses: `idea`, `ready`, `in-progress`, `on-hold`, `dropped`.
If dropping, ask the user whether to keep the file (for history) or delete it — default to
keeping it with status `dropped` unless told otherwise.

### Remove a completed item

Delete `specs/backlog/<slug>.md`, remove its row from `specs/backlog.md`, and add a one-line
entry to `CHANGELOG.md`. (Normally done automatically at the end of the `feature-spec` workflow —
use this only if the user asks to clean up manually.)

## Constraints

- Never invent scope the user didn't provide — capture what they said, nothing more.
- Don't create a `specs/YYMMDD-<slug>/` spec directory from this skill — that's `feature-spec`'s job.
