# nwtrack Backlog

## Purpose

This document is the current backlog of proposed features and ideas for `nwtrack`. It replaces
the old phase-numbered `specs/roadmap.md`. There is no required build order — priority is
whatever this table says right now, and reordering is just moving a row.

See `specs/mission.md` and `specs/tech-stack.md` for the product constitution that every backlog
item must still respect. Completed work is logged in `CHANGELOG.md`, not here.

## Statuses

- `idea` — captured, not yet spec-ready; may still need scoping
- `ready` — scoped enough to start a feature spec via the `feature-spec` skill
- `in-progress` — an active spec/branch exists under `specs/`
- `on-hold` — previously scoped, deliberately paused (reason noted in the item file)
- `dropped` — considered and rejected; kept for history, reason noted in the item file

## Backlog

| Status | Item | One-liner |
|---|---|---|
| ready | [HTML graphical reports](backlog/html-graphical-reports.md) | Export net worth/account history as self-contained HTML charts |
| idea | [Reporting UX options](backlog/reporting-ux-options.md) | Long/wide history layout, CSV output for aggregated history reports |
| idea | [Single-currency conversion reporting](backlog/single-currency-conversion-reporting.md) | Convert mixed-currency balances to one reporting currency |
| idea | [CLI retirement](backlog/cli-retirement.md) | Drop Typer once the TUI covers everything and is validated |
| idea | [Alembic migrations](backlog/alembic-migrations.md) | Replace hand-rolled SchemaManager with versioned migrations |

## Working the backlog

1. Capture a new idea as `specs/backlog/<slug>.md` (status `idea`) and add a row here. A stub is
   fine — problem statement and rough scope, nothing more.
2. Promote an item to `ready` once it's scoped enough to spec confidently.
3. Use the `feature-spec` skill to turn a `ready` item into a full spec directory
   (`specs/YYMMDD-<slug>/`) and a feature branch. The skill flips the item's status to
   `in-progress`.
4. On completion, remove the row and delete the item file, move the feature's spec directory
   from `specs/YYMMDD-<slug>/` to `specs/archive/<slug>/`, and add a one-line entry to
   `CHANGELOG.md` instead — this file only tracks what's still open.
