# Phase 39: TUI Visual Design System — Requirements

## Problem

TUI screens have accumulated incrementally since Phase 25 without a shared visual
design system. Colors, spacing, and small style patterns (error labels, hint text,
modal containers, titles) are hand-authored per screen in ad-hoc `DEFAULT_CSS`
blocks. There is no dark/light mode, and no single place to change a color or
spacing value across the app. This phase adds one reusable theme module that all
screens reference and revisits existing screens for layout/spacing consistency
under it.

## Scope

### In scope

- A shared Textual theme module (`entrypoints/tui/theme.py`) that defines:
  - Semantic color tokens layered on top of Textual's built-in `$primary`,
    `$surface`, `$error`, `$text-muted`, etc. — not a full replacement of
    Textual's palette, but a small set of nwtrack-specific semantic names
    (e.g. success/warning color, muted hint text, header accent) so screens stop
    hardcoding raw color values.
  - Shared spacing constants (padding/margin values) used consistently for modal
    containers, form fields, and section gutters.
  - Reusable CSS classes for patterns repeated across screens: modal container
    (`align: center middle`, `border: thick $primary`, `background: $surface`,
    padding), form title, error label, hint/muted label, button row.
  - A light color-variable override set, switched via Textual's built-in
    `App.dark` boolean (see Decisions).
- Wiring every existing screen (home, reports menu, admin menu, balance update,
  balance edit, accounts + account form, net worth history, aggregation, account
  balance history, roll forward, transfer, categories, institutions, tags, month
  picker, confirm modal) to reference the shared theme/classes instead of
  duplicating CSS, where a screen's current CSS overlaps with a shared pattern.
  Screens keep screen-specific CSS only for layout that is genuinely unique to
  that screen (e.g. table column widths).
- A global keybinding that toggles dark/light mode from any screen via
  `App.dark`, plus a small always-visible indicator of the current mode on the
  home screen (e.g. in the subtitle or a footer-adjacent label).
- Layout and spacing polish pass across existing screens for visual hierarchy
  (e.g. consistent use of titles, consistent error/hint placement, consistent
  modal sizing) — visual only, no workflow or navigation changes.
- `ruff`, `mypy`, and `pytest` pass.

### Out of scope / non-goals

- No new screens, workflows, or business logic.
- No new or changed navigation paths, menu structure, or keybindings beyond the
  single dark/light toggle. Existing key bindings (Escape to back out, `m`/`r`/`t`
  workflow shortcuts, etc.) are unchanged.
- No persistence of the dark/light choice across app restarts — it always starts
  in the default mode.
- No CLI-side visual changes — this phase is TUI-only (Rich CLI presenters are
  untouched).
- No accessibility audit or WCAG contrast certification; "reasonable contrast in
  both modes, terminal-safe colors" is the bar, not a formal audit.
- No changes to `entrypoints/tui/utils.py` business logic (e.g. `months_to_grid`).

## Data / Domain Impact

None. This phase touches only `entrypoints/tui/` presentation code. No ORM,
repository, use case, or CLI changes.

## Decisions

- **Dark/light mechanism**: Use Textual's built-in `App.dark: bool` reactive
  rather than a fully custom variable-switching scheme. Textual already flips
  its built-in `$`-prefixed variables (`$surface`, `$panel`, `$boost`, etc.)
  based on `App.dark`. The shared theme module layers nwtrack-specific semantic
  tokens on top and defines only the deltas needed for those tokens in light vs.
  dark mode (via Textual's CSS variable override mechanism, e.g. `:light`-style
  overrides or a small computed set applied in `on_mount`/`watch_dark`).
  Rationale: reuses Textual's already-correct light/dark base palette instead of
  re-deriving one, minimizing maintenance surface.
- **Toggle placement**: A global `Binding("ctrl+t", "toggle_dark", ...,
  priority=True)` registered on `NWTrackApp` (not per-screen) so it works from
  any screen. `priority=True` is required, not optional: form modals
  auto-focus an `Input` on mount, and a non-priority letter binding is
  swallowed by the focused `Input` instead of reaching the app (confirmed via
  a headless regression test before settling on this — see
  `tests/entrypoints/tui/test_theme_toggle.py::test_toggle_works_while_input_is_focused_in_a_modal`).
  A plain letter key (originally `"d"`) was also found to collide with the
  existing `Binding("d", "delete", "Delete")` used on every admin list screen
  (accounts, institutions, tags, categories) — `ctrl+t` avoids both problems:
  it isn't typeable text, so `priority=True` doesn't block users from typing
  `t`/`d`/etc. into any input field, and it doesn't collide with any existing
  binding. Not persisted — resets to the default (dark) on every launch. The
  home screen shows the current mode (e.g. `sub_title = "Dark mode" / "Light
  mode"`) as the lightweight indicator; no dedicated settings screen.
- **Color palette source**: No external brand palette provided. Use Textual's
  default theme variables as the base and choose nwtrack's semantic accent/
  success/warning colors from Textual's standard named colors, favoring
  terminal-safe / 16–256-color-compatible choices over true-color-only values,
  since this is a terminal app that should render reasonably across common
  terminal emulators.
- **Scope of the CSS consolidation**: Prefer moving *repeated* patterns (modal
  container chrome, error/hint label styling, form title styling, button rows)
  into shared CSS classes screens apply via `classes=`. Screen-unique layout
  (specific widths, specific table column setups) stays local to the screen.
  This avoids a big-bang rewrite while removing the real duplication.
- **Navigation/menu changes**: Explicitly excluded per roadmap wording ("without
  changing underlying screen workflows or navigation"). Home/menu screens get
  visual polish (alignment, spacing, list styling) but keep their existing
  `ListView`-based navigation and keybindings unchanged.

## CLI / TUI Behavior

- Launching `nwtrack tui launch` behaves exactly as before, defaulting to dark
  mode (Textual's own default).
- Pressing the new toggle binding from any screen flips `App.dark` and the
  visual theme updates live; the user's place in the screen stack is preserved.
- All screens render with consistent modal chrome, spacing, and label styling
  post-refactor; no screen's functional behavior (data displayed, workflow
  steps, validation) changes.

## Validation and Error Cases

- N/A — this phase has no new user input, validation rules, or error paths. The
  only new interactive surface is the theme toggle keybinding, which cannot
  fail (it flips a boolean).
- Regression risk: refactoring each screen's `DEFAULT_CSS` to use shared classes
  must not change functional widget IDs/queries (`query_one("#...")` calls) —
  only class-based styling is added/consolidated, not ID-based selectors.

## Feature-Specific Testing and Quality Checks

See `validation.md` for the full breakdown. Summary:

- Automated: a smoke test that `NWTrackApp.dark` toggles on the bound key and
  that the home screen reflects the mode in its subtitle. Existing TUI screen
  tests in `tests/entrypoints/tui/` continue to pass unmodified (behavioral
  assertions, not visual ones, so a CSS/theme refactor should not break them).
- Manual: visually walk each screen in both dark and light mode.
- Quality gates: `ruff`, `mypy`, `pytest` (per `specs/tech-stack.md`).

## Acceptance Criteria

- `src/nwtrack/entrypoints/tui/theme.py` exists and defines the shared color
  tokens, spacing constants, and reusable CSS class strings/snippets.
- Every screen listed in "In scope" references the shared theme module (either
  by importing constants/snippets into its `DEFAULT_CSS`, or by applying shared
  CSS classes to widgets) rather than duplicating modal-chrome / error-label /
  hint-label CSS verbatim.
- A global keybinding toggles `App.dark`; the home screen subtitle (or
  equivalent visible indicator) reflects the current mode.
- No navigation, menu structure, or existing keybinding changes anywhere.
- `ruff`, `mypy`, and `pytest` all pass.
- Manual walkthrough (documented in `validation.md`) confirms every screen is
  legible and visually consistent in both modes.
