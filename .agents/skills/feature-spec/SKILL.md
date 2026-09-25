---
name: feature-spec
description: Kicks off a new feature by picking an item from specs/backlog.md, creating a git branch, interviewing the user about scope/decisions/context, and writing a spec directory under specs/ containing plan.md, requirements.md, and validation.md. Trigger when the user says "feature spec", "start the next feature", "work on <backlog item>", or invokes /feature-spec.
---

# Feature Spec

## Workflow

### 1. Pick a backlog item

Read `specs/backlog.md`. If the user named a specific item, use it (promote it to `ready` if it
was still an `idea`, and note that in the backlog file's frontmatter). Otherwise, list the
`ready` items (falling back to `idea` items if none are `ready`) and use `Ask User Question` to
let the user pick one.

Read that item's `specs/backlog/<slug>.md` file for existing context before the interview.

### 2. Create the branch

```
git checkout devel
git checkout -b feature/<slug>
```

### 3. Interview the user — BEFORE writing any files

Enter /plan mode to interview the user about the feature and gather information for the spec.

Use `Ask User Question` tool with questions in the following categories:

| Header | Question focus |
|--------|---------------|
| **Scope** | What the feature collects, exposes, or does — fields, behaviour, data shape |
| **Decisions** | Key implementation choices — storage, visibility, validation, UX pattern |
| **Context** | Tone, constraints, or anything shaping the spec — copy style, stack limits, open questions |

Write files to disk after the user has answered the questions.

### 4. Read guidance files

Read `specs/mission.md` and `specs/tech-stack.md` before drafting.

### 5. Create the spec directory

Name: `specs/YYMMDD-<slug>/` using today's date and the backlog item's slug.

#### `requirements.md`
- Scope section: what is and is not included; field/data table if applicable
- Decisions section: choices made and why (draw from user answers)
- Context section: tone rules, stack pointers, existing patterns to follow

#### `plan.md`
- Numbered task groups appropriate to the feature (for example: Data → Components → Page & Route → Navigation → Tests)
- Each group has numbered sub-tasks; groups should be independently implementable

#### `validation.md`
- Automated: project test and typecheck commands pass; specific assertions required
- Manual: walkthrough, behaviour, edge cases
- Tone check if the feature has user-facing copy
- Definition of done
- Checklist of completed validation steps including testing and code quality checks, aligned with `plan.md` task groups

### 6. Update the backlog

Set the item's status to `in-progress` in `specs/backlog/<slug>.md` and in the `specs/backlog.md`
table.

## When the feature ships

This is out of scope for this skill's own workflow, but remind the user: once the feature spec's
`validation.md` definition of done is met and merged, remove the item's row from
`specs/backlog.md`, delete `specs/backlog/<slug>.md`, move `specs/YYMMDD-<slug>/` to
`specs/archive/<slug>/`, and add a one-line entry to `CHANGELOG.md`.

## Constraints

- Respect the existing tech stack defined in `specs/tech-stack.md` — no new dependencies without user approval
- Follow existing conventions and patterns already established in the codebase
- Keep feature scope focused and independently shippable
