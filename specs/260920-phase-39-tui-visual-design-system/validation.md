# Phase 39: TUI Visual Design System — Validation

## Automated Tests

- **New**: `tests/entrypoints/tui/test_theme_toggle.py`
  - Using `NWTrackApp.run_test()`, assert `app.dark` starts at Textual's
    default value.
  - Simulate the toggle binding's keypress (`pilot.press(<key>)`) and assert
    `app.dark` flips to the opposite value.
  - Assert the home screen's visible mode indicator (`sub_title` or equivalent)
    updates to match, both on initial mount and after toggling.
  - Toggle twice and confirm it returns to the original state (idempotent
    round-trip, no drift).
- **Regression**: run the full existing `tests/entrypoints/tui/` suite
  unmodified — these assert on widget IDs, queried values, and workflow
  behavior, not on CSS content, so a pure styling refactor must leave every one
  of them green. Any failure here indicates the CSS consolidation accidentally
  changed a widget ID, removed a queried element, or altered layout in a way
  that broke a behavioral assertion (e.g. `DataTable` row/column counts).
- Confirm `theme.py` has no runtime side effects at import time beyond defining
  constants/strings (safe to import from `app.py` and every screen without
  triggering DB/session work).

## Manual Validation

Walk every in-scope screen once in dark mode and once in light mode
(toggle via the new keybinding mid-session, not just at two separate
launches, to confirm live re-styling works without restart):

- [ ] Home screen — menu list legible, mode indicator visible and correct in
      both modes.
- [ ] Reports menu, Admin menu — list styling consistent with home.
- [ ] Balance update screen — grid legible, right-justified amount column
      unchanged, month/roll-forward/transfer shortcuts still work.
- [ ] Balance edit modal — modal chrome (border, padding, title) matches other
      modals; error message (invalid amount) still displays correctly.
- [ ] Accounts list screen + Account form modal (create and edit) — form
      fields legible, error/hint label placement matches other modals.
- [ ] Net worth history screen — table, Delta column, Total row, status-scope
      selector all legible; no regression from Phase 33.
- [ ] Aggregation screen — dimension + status-scope selectors, grouped table
      legible in both modes.
- [ ] Account balance history screen — account select, Start/End buttons,
      month picker modal, table (Month/Balance/Delta), summary label legible;
      right-justified numeric columns preserved.
- [ ] Roll forward modal, Transfer modal — modal chrome consistent, source/
      month pickers still function.
- [ ] Categories, Institutions, Tags list screens + their form modals — CRUD
      forms legible, error/hint styling consistent.
- [ ] Month picker modal, Confirm modal — chrome consistent with other modals.
- [ ] Confirm that pressing the toggle keybinding from a screen deep in the
      navigation stack (e.g. inside a modal) does not crash or pop the screen
      stack unexpectedly.
- [ ] Confirm no existing keybinding (Escape, `m`, `r`, `t`, `ctrl+s`, `q`)
      changed behavior or was shadowed by the new toggle binding.
- [ ] Spot-check color contrast by eye in a standard terminal (e.g. Terminal.app
      or iTerm2) in both modes — text should be readable against backgrounds,
      no near-invisible muted text.

## Quality Checks

- [ ] `just lint` (ruff) passes with no new warnings.
- [ ] `just typecheck` (mypy) passes.
- [ ] `just test` (full pytest suite) passes, including the new theme-toggle
      test and the full unmodified `tests/entrypoints/tui/` suite.

## Regression / Compatibility Risks

- CSS class consolidation must not rename or remove any widget `id=` used by
  `query_one(...)` in screen code — verified by code review per screen during
  step 3 of `plan.md`, and confirmed indirectly by the existing test suite
  staying green.
- The new global toggle binding must not collide with any existing per-screen
  `Binding` key (survey: `escape`, `q`, `m`, `r`, `t`, `ctrl+s` are already in
  use across various screens — the new binding must avoid all of them).
- No CLI-visible change is expected; `tests/entrypoints/` CLI tests (outside
  `tests/entrypoints/tui/`) must remain untouched and green, confirming this
  phase did not leak into the Rich/CLI presentation layer.

## Definition of Done

- All items in "Automated Tests" and "Manual Validation" are checked.
- `ruff`, `mypy`, and `pytest` all pass (per `specs/tech-stack.md` required
  gates).
- `specs/roadmap.md` Phase 39 is marked `[X]` with outcomes matching what was
  actually shipped.
