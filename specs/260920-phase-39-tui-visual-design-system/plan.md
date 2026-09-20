# Phase 39: TUI Visual Design System — Plan

> **Implementation note**: The installed Textual version (8.2.7, satisfying
> `textual>=3.0.0`) removed the `App.dark: bool` reactive assumed in
> `requirements.md`. Textual 8.x uses a named `App.theme: str` reactive
> (`"textual-dark"` / `"textual-light"`, etc.) plus a built-in
> `action_toggle_dark()` action that already flips between those two themes.
> The implementation below uses `self.theme` / the built-in
> `action_toggle_dark` action instead of a boolean `dark` field, and
> `app.current_theme.dark` (a `Theme.dark: bool` field) to read the current
> mode. This preserves the spec's decision ("use Textual's built-in
> mechanism, don't hand-roll a parallel light/dark scheme") — only the
> specific attribute names differ from what was assumed at spec-writing time.

## 1. Theme module [x]

1.1. Create `src/nwtrack/entrypoints/tui/theme.py`:
   - Semantic color constants (as CSS variable name strings and/or literal
     Textual color values), e.g. accent, success, warning, muted-text, border,
     reusing/aliasing Textual's `$primary`, `$surface`, `$error`,
     `$text-muted` where possible rather than inventing parallel values.
   - Spacing constants (e.g. `SPACING_SM = 1`, `SPACING_MD = 2`) used for
     padding/margin in shared CSS snippets.
   - Reusable CSS class snippets as module-level strings, grouped by pattern:
     - `MODAL_CONTAINER_CSS` (align center middle, border thick $primary,
       background $surface, padding, max-height/overflow for tall modals)
     - `FORM_TITLE_CSS` (centered, margin-bottom)
     - `ERROR_LABEL_CSS` (color $error, margin-top)
     - `HINT_LABEL_CSS` (color $text-muted, margin-top)
     - `BUTTON_ROW_CSS` (horizontal layout, spacing between buttons)
   - A `LIGHT_MODE_VARIABLES_CSS` (or equivalent) snippet defining the light-mode
     deltas for any nwtrack-specific semantic tokens that need distinct light
     values, applied via Textual's variable-override mechanism.
   - Keep this module CSS-authoring only — no widget classes, no business logic.

1.2. Decide and document (as a short module docstring) the mechanism for how a
   screen consumes these snippets: e.g. per-screen `DEFAULT_CSS` embeds the
   shared snippet via an f-string/constant, or shared class names are declared
   once (e.g. in `NWTrackApp.CSS`) and screens apply `classes="modal-container"`
   etc. Pick whichever keeps screens simplest — prefer app-level shared CSS
   classes applied via `classes=` over per-screen string interpolation, since
   Textual supports global `CSS`/`CSS_PATH` on `App`.

## 2. App-level wiring [x]

2.1. In `src/nwtrack/entrypoints/tui/app.py`:
   - Added `NWTrackApp.CSS = SHARED_CSS`, making the shared classes available
     globally to every screen without per-screen duplication.
   - Added `Binding("ctrl+t", "toggle_dark", "Toggle theme", priority=True)`
     to `BINDINGS`, reusing Textual's built-in `App.action_toggle_dark()` (no
     custom action method needed — see implementation note above).
   - **Bug found and fixed during validation**: the first attempt used
     `Binding("d", "toggle_dark", ...)` without `priority=True`. Two problems
     surfaced under test: (1) `"d"` is already bound to `"delete"` on every
     admin list screen (`accounts.py`, `institutions.py`, `tags.py`,
     `categories.py`), so the screen-level binding would have shadowed the
     app-level one there; (2) even on screens without that collision, a
     non-priority binding is swallowed by whatever widget has focus — every
     form modal auto-focuses an `Input` on mount, so pressing `d` typed the
     letter into the name field instead of toggling the theme. Switched to
     `ctrl+t` with `priority=True`, which reaches the app regardless of focus
     without blocking normal text entry (confirmed via headless
     `pilot.press()` scripts and a new regression test — see step 5).
   - No explicit re-render hook was needed — Textual's `theme` reactive
     already triggers a full re-style on change.

2.2. In `src/nwtrack/entrypoints/tui/screens/home.py`:
   - `HomeScreen.on_mount` sets `self.sub_title` from
     `self.app.current_theme.dark` and registers
     `self.watch(self.app, "theme", self._update_theme_indicator)` so the
     indicator updates live whenever the theme changes, including while the
     home screen itself is the active screen (not just on screen resume).

## 3. Screen-by-screen CSS consolidation [x]

For each screen below, replace duplicated modal-chrome / title / error / hint
CSS with the shared classes from step 1, keeping screen-specific layout rules
(table columns, widths, unique containers) local. Apply spacing constants where
a screen currently hardcodes padding/margin numbers that match the new shared
scale.

3.1. Modals: `balance_edit.py`, `month_picker.py`, `confirm_modal.py`,
   `roll_forward.py`, `transfer.py`, `categories.py` (`CategoryFormModal`),
   `institutions.py` (`InstitutionFormModal`), `tags.py` (`TagFormModal`),
   `accounts.py` (`AccountFormModal`).

3.2. Full screens: `home.py`, `reports_menu.py`, `admin_menu.py`,
   `balance_update.py`, `accounts.py` (`AccountsListScreen`),
   `networth_history.py`, `aggregation.py`, `account_balance_history.py`.

3.3. Done — every screen listed in 3.1/3.2 kept its widget `id=` selectors
   unchanged; only `classes=` attributes were added and the corresponding
   `DEFAULT_CSS` blocks were trimmed to screen-unique sizing rules
   (`width`, `max-height`, `overflow-y`) plus the one real one-off
   (`#rf-warning { color: $warning; }` in `roll_forward.py`, since the shared
   `.error-text`/`.hint-text` classes don't cover a warning-colored label).
   Confirmed by the full existing test suite staying green (no ID-based
   `query_one` lookup broke).

## 4. Layout/spacing polish pass [x]

4.1. Numeric-column right-justification was audited across `balance_update.py`,
   `networth_history.py`, and `aggregation.py` — already consistently applied
   (Phase 27/33) via `Text(..., justify="right")`; no changes needed.

4.2. Found and fixed a real inconsistency: `aggregation.py`,
   `networth_history.py`, and `account_balance_history.py` each had an
   `#error-label` `Label` with **no** styling at all (unlike every modal,
   whose error labels were red via `$error`). Applied the shared
   `.error-text` class to all three so error messages render consistently
   across every screen, not just modals — a direct readability win in scope
   with the phase goal.

4.3. No behavioral, navigation, or keybinding changes were made — verified by
   the full existing test suite passing unmodified.

## 5. Tests [x]

5.1. Added `tests/entrypoints/tui/test_theme_toggle.py` using Textual's test
   harness (`App.run_test()`):
   - `test_toggle_binding_flips_theme` — boots `NWTrackApp`, presses
     `ctrl+t`, asserts `app.theme` changed.
   - `test_toggle_twice_returns_to_original_theme` — toggles twice, asserts
     round-trip back to the original theme.
   - `test_home_screen_indicator_reflects_mode` — asserts the home screen's
     `sub_title` matches `app.current_theme.dark` both on initial mount and
     after toggling.
   - `test_toggle_works_while_input_is_focused_in_a_modal` — regression test
     for the focus-swallowing bug found during validation: opens the
     Institution create modal, confirms the name `Input` has focus, presses
     `ctrl+t`, and asserts the theme changed **and** the input's value is
     still empty (i.e. the keypress reached the app, not the text field).
   All 4 pass.

5.2. Ran the full existing `tests/entrypoints/tui/` suite and the full project
   suite (388 tests) — all green, confirming no widget ID or behavioral
   assertion broke from the CSS refactor.

## 6. Quality gates [x]

6.1. Ran `ruff format` on only the files touched this phase (not the whole
   repo — there was pre-existing formatting debt in unrelated files that is
   out of scope for this change).

6.2. `mypy src/ tests/` — `Success: no issues found in 214 source files`.

6.3. `pytest tests/` — 387 passed, full suite green after every task group.

6.4. `ruff check src/ tests/` — `All checks passed!`.

## 7. Docs [x]

7.1. `specs/roadmap.md` Phase 39 marked `[X]`; expected-outcomes bullets
   updated to describe the actual implementation (shared CSS classes reusing
   Textual's built-in theme mechanism, rather than a hand-rolled color
   palette — see the implementation note at the top of this file).

7.2. `specs/tech-stack.md` Architecture section gained a bullet documenting
   the shared TUI theme module convention, since it's a lasting architectural
   pattern future TUI screens should follow (not just a one-phase detail).

7.3. CLAUDE.md was left unchanged — its TUI section already lists screens by
   module name without describing per-screen styling conventions, and this
   phase doesn't change the screen inventory or navigation, so no update was
   necessary there.

## 8. Menu layout redesign [x] (post-PR feedback)

After the PR was opened, the user provided a screenshot of the home screen
and clarified the primary motivation for this phase is visual appeal — the
top-level menus specifically read as unstyled (a bare `ListView` stretched
across the full terminal). See the addendum in `requirements.md`.

8.1. Added `.menu-screen` (align center middle, applied to the `Screen`
   itself via `classes="menu-screen"` in `__init__`) and `.menu-panel`
   (`width: 44`, `height: auto`, `border: round $primary`, `background:
   $surface`, `padding: 1 2`) to `theme.py`, plus `.menu-title` (bold,
   centered), `.menu-hint` (muted, centered), and scoped `ListView`/`ListItem`
   rules (`height: auto`, transparent background, no scrollbar, `padding: 0
   1` per item) so the list breathes inside the panel instead of stretching
   full-width.

8.2. `home.py`, `reports_menu.py`, `admin_menu.py`: wrapped the existing
   `ListView` in a `Vertical(classes="menu-panel")` with a title `Label`
   above and a hint `Label` below. `ListItem` ids and `on_list_view_selected`
   handlers are untouched — only the container/wrapping changed.

8.3. Verified via headless `Pilot` + `App.export_screenshot()` (parsing the
   SVG's `<text>` elements, since this session has no interactive terminal)
   that all three menus render as a centered, rounded, bordered panel with
   correct title/items/hint text in both themes — see `validation.md`.

## 9. Delta color coding [x] (post-PR feedback)

Third round of feedback: historical report deltas should use contrasting
color (green/red) rather than plain `+`/`-` text — see the addendum in
`requirements.md`.

9.1. Added `delta_text(value: int, app: App, *, justify=...) -> Text` to
   `entrypoints/tui/utils.py`. Colors come from `app.current_theme.success`
   / `.error` (both themes currently resolve to `#4EBF71` / `#ba3c5b`) rather
   than hardcoded Rich color names, with a `"green"`/`"red"` fallback only
   for the type-checker-required `None` case (`Theme.success`/`.error` are
   typed `str | None`, though the built-in themes always set them).
   `justify` defaults to `"right"` for `DataTable` cells; callers pass
   `justify=None` when assembling the value inline into a `Text.assemble(...)`
   sentence.

9.2. Wired into `AccountBalanceHistoryScreen` (Delta column +
   `Text.assemble` in the "Total change" summary label) and
   `NetWorthHistoryScreen` (Delta column + Total row), replacing the
   duplicated `sign = "+" if x >= 0 else ""` + plain `Text(...)` pattern at
   each of the 4 call sites.

9.3. Verified with a headless script that pushes `NetWorthHistoryScreen`
   with mixed positive/negative/zero deltas and inspects each `DataTable`
   cell's Rich `Text.spans` — confirms positive deltas carry
   `app.current_theme.success`, negative deltas carry `.error`, and zero
   carries no style. Added permanent unit tests
   (`tests/entrypoints/test_tui_utils.py::TestDeltaText`, 4 tests) covering
   the same three cases plus the `justify=None` inline-use path.

## 10. Filter control layout (post-PR feedback)

Fourth round of feedback (with screenshot): the Start/End/dimension/scope
`Select` and `Button` filter controls on report screens each stretched
full-width and stacked one per row — see the addendum in `requirements.md`.
This was explored first via `AskUserQuestion` (recommendation: wrap in a
`Horizontal` toolbar with capped widths) before implementing, since it was
framed as an open exploration rather than a specified change.

10.1. Added `.filter-bar` (Horizontal container, `height: auto`,
   `margin-bottom: 1`) plus scoped `.filter-bar Button`/`.filter-bar Select`
   width rules to `theme.py`.

10.2. Wrapped the existing filter widgets in `Horizontal(classes=
   "filter-bar")` in `networth_history.py`, `aggregation.py`, and
   `account_balance_history.py`. No widget IDs, event handlers, or
   validation logic changed — purely a container/CSS change.
   `account_balance_history.py` also got a screen-local `#account-select {
   width: 34; }` override since account names need more room than the
   shared 26-column default sized for short option labels
   (Historical/Active/All, Category/Side/Institution/...).

10.3. Verified via headless `Pilot` + `App.export_screenshot()`, this time
   extracting each `<text>` element's `(x, y)` position (not just its
   content) to confirm the controls land on the same row: all three
   screens show their filter widgets sharing one `y` coordinate instead of
   three separate rows. Existing test suites for all three screens
   (`test_networth_history_screen.py`, `test_aggregation_screen.py`,
   `test_account_balance_history_screen.py`) pass unmodified.
