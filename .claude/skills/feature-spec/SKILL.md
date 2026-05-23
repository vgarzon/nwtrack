---
name: feature-spec
description: Kicks off a new feature by finding the next incomplete phase in specs/roadmap.md, creating a git branch, interviewing the user about scope/decisions/context, and writing a spec directory under specs/ containing plan.md, requirements.md, and validation.md.  Trigger when the user says "feature spec", "next phase", "start the next feature", or invokes /feature-spec.
---

# Feature Spec

## Workflow

### 1. Find the next phase

Read `specs/roadmap.md`. The next phase is the first section whose items are all `[ ]`. Note its name to derive the branch and directory name.

### 2. Create the branch

```
git checkout -b phase-NN-<kebab-name>

```

### 3. Ask user for initial instruction or context

Ask user if there are any preable they want to provide before you start asking the three main questions.  Input can be in the form of general instructiones or content from a file.  For example: Input file format and instructions provided in a markdown file.

### 4. Interview the user — BEFORE writing any files

Use `Ask User Question` tool with exactly **3 questions in one call**:


| Header | Question focus |
|--------|---------------|
| **Scope** | What the feature collects, exposes, or does — fields, behaviour, data shape |
| **Decisions** | Key implementation choices — storage, visibility, validation, UX pattern |
| **Context** | Tone, constraints, or anything shaping the spec — copy style, stack limits, open questions |


Do **not** write any files until the user has answered all three questions.

### 5. Read guidance files

Read `specs/mission.md` and `specs/tech-stack.md` before drafting.

### 6. Create the spec directory

Name: `specs/YYMMDD-phase-NN-<feature-name>/` using today's date.

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

### 7. Write additional files as needed

If user provided instructions or content in step 3, write those files into the spec directory.  For example, if they provided a markdown file with input format and instructions, save that file as `specs/YYMMDD-phase-NN-<feature-name>/input-formaat.md`.

### 8. Ask user about missing details

User the `Ask User Question` tool to ask any follow-up questions needed to fill in gaps in the spec.  Skip this step if the spec is already sufficiently detailed and clear.

## Constraints

- Respect the existing tech stack defined in `specs/tech-stack.md` — no new dependencies without user approval
- Follow existing conventions and patterns already established in the codebase
- Keep feature scope focused and independently shippable
