---
name: feature-spec
description: Kicks off a new feature by picking an item from specs/backlog.md, creating a git branch, reading the constitution and relevant code, interviewing the user only about unresolved scope/surface/data-impact/edge-case questions, and writing a spec directory under specs/ containing plan.md, requirements.md, and validation.md. Trigger when the user says "feature spec", "start the next feature", "work on <backlog item>", or invokes /feature-spec.
---

# Feature Spec

Lifecycle: **`feature-spec`** → `feature-implement` → `feature-close`

**Starts from:** a backlog item (`idea` or `ready`) and a clean `devel`.
**Ends with:** branch `feature/<slug>`, a spec directory `specs/YYMMDD-<slug>/`, and the item
marked `in-progress`. Nothing is committed or pushed by this skill.
**Next:** `feature-implement`, which commits these docs and builds the feature.

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

### 3. Ask user for initial instruction or context

Ask the user for any preamble they want to provide before you research and interview. Input can
be general instructions or content from a file (for example input file format and instructions
in a markdown file). Keep what they give you; step 5 must not re-ask it.

### 4. Read guidance and relevant code — BEFORE interviewing

Read `specs/mission.md` and `specs/tech-stack.md`, the backlog item, the preamble, and the code
the feature will touch or imitate (neighbouring use cases, presenters, CLI/TUI screens,
repositories, existing specs under `specs/archive/`). Use this to:

- list what the preamble and the code already settle (these become decisions, not questions);
- find the real unknowns, and the recommended answer to each from existing conventions;
- note cross-cutting interactions (CLI startup callbacks, schema/migrations, CSV round trip,
  existing user data) that the feature may touch.

### 5. Interview the user — BEFORE writing any files

Use `Ask User Question` with **2–4 questions in one call**. Ask only about dimensions that are
still unresolved after step 4, and mark the recommended option first. Candidate dimensions:

| Header | Settles |
|--------|---------|
| **Scope** | Behaviour, inputs/outputs, data shape — and explicit non-goals |
| **Surface** | CLI, TUI, or both; UX shape. New report surfaces should target both (see `tech-stack.md`) |
| **Data impact** | Schema change or migration, CSV export/import round trip, effect on an existing database, safety of production data |
| **Edge cases & proof** | Failure modes that matter, and what `validation.md` must prove |

Rules:

- Skip any dimension the preamble or code already answers; never re-ask what the user said.
- Use the `preview` field when options are visual or numeric: CLI output mockups, TUI layouts,
  or a small table of sample values the user should approve (tunable data, copy, defaults).
- Free-text context comes through the tool's built-in "Other" option; no separate Context
  question.
- Anything inferred rather than asked goes into `requirements.md` under "Assumptions and open
  questions" (step 6), never into the spec as a silent fact.

Do **not** write any files until the user has answered.

### 6. Create the spec directory

Name: `specs/YYMMDD-<slug>/` using today's date and the backlog item's slug.

#### `requirements.md`
- Scope section: what is and is not included; field/data table if applicable
- Non-goals section: what this feature deliberately does not do
- Decisions section: choices made and why (draw from user answers)
- Context section: tone rules, stack pointers, existing patterns to follow
- Assumptions and open questions section: every inference made without asking, and anything
  still unresolved, so the user can correct it before implementation

#### `plan.md`
- Numbered task groups appropriate to the feature (for example: Data → Components → Page & Route → Navigation → Tests)
- Each group has numbered sub-tasks; groups should be independently implementable

#### `validation.md`
- Automated: project test and typecheck commands pass; specific assertions required
- Manual: walkthrough, behaviour, edge cases
- Tone check if the feature has user-facing copy
- Definition of done

### 7. Write additional files as needed

If user provided instructions or content in step 3, write those files into the spec directory.
For example, if they provided a markdown file with input format and instructions, save that file
as `specs/YYMMDD-<slug>/input-format.md`.

### 8. Ask user about missing details

Use the `Ask User Question` tool for follow-up questions needed to fill gaps or resolve open
questions listed in `requirements.md`, then update that section. Skip this step if the spec is
already sufficiently detailed and clear.

### 9. Update the backlog

Set the item's status to `in-progress` in `specs/backlog/<slug>.md` and in the `specs/backlog.md`
table.

## Hand-off

Leave the new files uncommitted and tell the user the next step is `feature-implement`
(commit the spec docs, build the feature, open the PR) and then `feature-close` (archive,
changelog, merge). Do not repeat their steps here.

## Constraints

- Respect the existing tech stack defined in `specs/tech-stack.md` — no new dependencies without user approval
- Follow existing conventions and patterns already established in the codebase
- Keep feature scope focused and independently shippable
