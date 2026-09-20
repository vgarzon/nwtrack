# Phase 39: TUI Visual Design System — Validation

## Automated Tests — done

- **New**: `tests/entrypoints/tui/test_theme_toggle.py` (4 tests, all pass):
  - `test_toggle_binding_flips_theme` — `ctrl+t` flips `app.theme`.
  - `test_toggle_twice_returns_to_original_theme` — round-trips back cleanly.
  - `test_home_screen_indicator_reflects_mode` — home `sub_title` tracks
    `app.current_theme.dark` on mount and live after toggling.
  - `test_toggle_works_while_input_is_focused_in_a_modal` — regression test
    for a real bug found during validation (see `plan.md` §2.1): confirms the
    toggle reaches the app even when a modal's `Input` has focus, and that
    the keypress does not leak into the input's value.
- **Regression**: the full existing `tests/entrypoints/tui/` suite (88 tests
  pre-phase) and the full project suite (388 tests post-phase) all pass
  unmodified — these assert on widget IDs, queried values, and workflow
  behavior, not on CSS content, so the styling refactor left every one of
  them green with no ID, query, or layout regression.
- Confirmed `theme.py` has no runtime side effects at import time beyond
  defining constants/strings (imported by `app.py` and every screen without
  triggering DB/session work; `mypy`/`ruff` clean).

## Manual Validation

This phase was implemented and validated in a non-interactive coding session
(no attached terminal to eyeball colors in). What could be verified
mechanically was verified via headless `Pilot`-driven checks and, where it
had lasting regression value, promoted into `test_theme_toggle.py`. What
requires an actual human eye on a real terminal is flagged below for the
user to spot-check — it was not rubber-stamped.

Verified mechanically (headless `pilot.press()`/`push_screen()`, both
themes):

- [x] Home screen — mode indicator (`sub_title`) correct on mount and live
      after toggling (`test_home_screen_indicator_reflects_mode`).
- [x] Admin menu → Institutions list → create modal — mounts, focuses the
      name input, applies `.modal-container`/`.modal-title`/`.error-text`
      without error in dark mode
      (`test_toggle_works_while_input_is_focused_in_a_modal`).
- [x] Admin menu → Categories list → create modal (`.modal-container`) and a
      standalone `ConfirmModal` (`.modal-container` +
      `.modal-container-warning` combined) both mount without error after
      switching to `"textual-light"` first
      (`test_full_screen_and_modals_mount_in_light_mode`).
- [x] Toggling while a modal's `Input` has focus does not crash the app,
      does not pop the screen stack, and does not leak the keypress into the
      input's value (same test as above).
- [x] No existing keybinding collides with the new one: `ctrl+t` was checked
      against every key string used by `Binding(...)` across all screens
      (`escape`, `q`, `c`, `d`, `m`, `r`, `t`, `ctrl+s` — see `plan.md` §2.1
      for the collision found and fixed with the original `"d"` choice).
- [x] Every screen in scope (all 17) passes its own existing test file
      unmodified after the CSS refactor — `tests/entrypoints/tui/` (88 tests)
      — meaning each one mounts, renders its `DataTable`/`Select`/form
      widgets, and responds to its documented keybindings exactly as before.

Not independently verified by this implementation pass — recommended
follow-up for the user with an interactive terminal:

- [ ] Eyeball every in-scope screen in both dark and light mode in a real
      terminal (Terminal.app / iTerm2) for genuine visual legibility —
      mechanical mounting success doesn't guarantee good-looking contrast.
- [ ] Spot-check color contrast — muted hint text (`$text-muted`) and warning
      text (`$warning`) against `$surface` in light mode specifically, since
      that's the newer, less-exercised of the two themes in this codebase.
- [ ] Confirm the `d`/`r`/`t`/`m`/`c` letter keys still type normally into
      every text `Input` (the `ctrl+t` choice was specifically made to avoid
      the `priority=True` + letter-key trap that breaks normal typing, but a
      live keyboard check is cheap insurance).

## Quality Checks — done

- [x] `ruff check src/ tests/` — `All checks passed!`
- [x] `ruff format` run on every file touched this phase (not repo-wide —
      pre-existing formatting debt in untouched files is out of scope).
- [x] `mypy src/ tests/` — `Success: no issues found in 214 source files`.
- [x] `pytest tests/` — 389 passed, including the 5 new theme-toggle tests
      and the full unmodified `tests/entrypoints/tui/` suite.

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

- [x] All automated tests and quality gates pass (see above).
- [x] `ruff`, `mypy`, and `pytest` all pass (per `specs/tech-stack.md`
      required gates).
- [x] `specs/roadmap.md` Phase 39 is marked `[X]` with outcomes matching what
      was actually shipped (including the `ctrl+t` binding and test count).
- [x] `specs/tech-stack.md` documents the shared theme module as a lasting
      architectural convention.
- [ ] Human spot-check of visual legibility/contrast in a real terminal — see
      the un-checked items under "Manual Validation" above; this is the one
      part of validation this implementation pass could not perform itself.
