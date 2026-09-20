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
   - Added `Binding("d", "toggle_dark", "Toggle theme")` to `BINDINGS`, reusing
     Textual's built-in `App.action_toggle_dark()` (no custom action method
     needed — see implementation note above). Confirmed `d` does not collide
     with any existing screen-level binding (`m`, `r`, `t`, `q`, `escape`,
     `ctrl+s`, `c` were the ones in use).
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
   - `test_toggle_binding_flips_theme` — boots `NWTrackApp`, presses `d`,
     asserts `app.theme` changed.
   - `test_toggle_twice_returns_to_original_theme` — toggles twice, asserts
     round-trip back to the original theme.
   - `test_home_screen_indicator_reflects_mode` — asserts the home screen's
     `sub_title` matches `app.current_theme.dark` both on initial mount and
     after toggling.
   All 3 pass.

5.2. Ran the full existing `tests/entrypoints/tui/` suite (88 tests) and the
   full project suite (387 tests) — all green, confirming no widget ID or
   behavioral assertion broke from the CSS refactor.

## 6. Quality gates

6.1. `just lint-fix` / `just format` to normalize the new/edited files.

6.2. `just typecheck` — confirm `theme.py` and touched screens type-check
   cleanly (CSS strings are just `str`, no typing concerns expected).

6.3. `just test` — full suite green.

## 7. Docs

7.1. Update `specs/roadmap.md` Phase 39 checkbox to `[X]` once complete, per
   the existing pattern from Phases 1–38.

7.2. If CLAUDE.md's TUI section needs a one-line mention of the shared theme
   module (it currently describes screens but not styling conventions), add a
   brief note — optional, only if it materially helps future navigation of the
   codebase.
