# nwtrack Bugs

## Purpose

Board of known defects in `nwtrack`. Kept separate from `specs/backlog.md`, which only lists
planned features. Priority is driven by severity, then by row order. Fixed bugs are removed from
this file; the pull request description is the permanent record of the root cause, and
`CHANGELOG.md` gets a `Fixed:` line when the bug was user-visible.

## Statuses

- `reported` — captured, not yet reproduced
- `confirmed` — reproduced; a failing test or repro command exists
- `in-progress` — a `fix/<slug>` branch exists
- `wontfix` — considered and rejected (reason noted in the bug file)
- `cannot-reproduce` — could not be reproduced (details noted in the bug file)

## Severities

- `critical` — data loss or corruption, failed migration
- `major` — wrong numbers in reports, or a crash in a primary workflow
- `minor` — cosmetic issues, edge cases

## Bugs

| Status | Severity | Item | One-liner |
|---|---|---|---|
| reported | minor | [transfer-modal-focus-stays-on-destination](bugs/transfer-modal-focus-stays-on-destination.md) | Transfer modal: focus stays on destination account instead of moving to the amount box |

## Working the bugs

See the `bug-fix` skill (`.claude/skills/bug-fix/SKILL.md`) and the "Bug Fixes" section of `CLAUDE.md`.
