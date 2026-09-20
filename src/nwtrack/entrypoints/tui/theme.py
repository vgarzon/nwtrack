"""Shared visual design tokens for the nwtrack TUI.

Textual (8.x) ships two built-in themes, "textual-dark" and "textual-light",
each defining a matching set of `$`-prefixed CSS variables (`$primary`,
`$surface`, `$error`, `$warning`, `$text-muted`, etc.). Toggling
`App.theme` between them (via the built-in `action_toggle_dark`) already
re-derives every one of those variables correctly for both modes, so this
module does not define a parallel color palette.

What screens actually duplicated was *structural* CSS: modal chrome (border,
background, padding), title/error/hint label styling, and button-row layout.
`SHARED_CSS` collects those repeated patterns as global classes, registered
once via `NWTrackApp.CSS`, so screens apply `classes="modal-container"` etc.
instead of re-declaring the same rules per screen. Screen-specific sizing
(width, max-height, table columns) stays local to each screen.

The `.menu-screen`/`.menu-panel` classes give the three top-level navigation
menus (home, reports, admin) a centered, bordered, fixed-width panel instead
of a bare `ListView` stretched across the full terminal — the same visual
language as the modal panels, applied to plain (non-modal) screens.

The `.filter-bar` class fixes the same "full-width block" default on report
screens' filter controls: a bare `Button`/`Select` yielded directly into a
`Screen` stretches to the full terminal width and stacks one per row (a
`Select`'s own `DEFAULT_CSS` doesn't set a width, so it falls back to the
container's `1fr`). Wrapping them in `Horizontal(classes="filter-bar")` and
capping each control's width turns Month/Start/End buttons and
dimension/scope `Select`s into a compact toolbar row above the table.
"""

SPACING_SM = 1
SPACING_MD = 2

SHARED_CSS = """
ModalScreen {
    align: center middle;
}

.modal-container {
    border: thick $primary;
    background: $surface;
    padding: 1 2;
    height: auto;
}

.modal-container-warning {
    border: thick $warning;
}

.modal-title {
    text-align: center;
    margin-bottom: 1;
}

.error-text {
    color: $error;
    margin-top: 1;
}

.hint-text {
    color: $text-muted;
    margin-top: 1;
}

.button-row {
    margin-top: 1;
    align: right middle;
    height: auto;
}

.button-row Button {
    margin-left: 1;
}

.menu-screen {
    align: center middle;
}

.menu-panel {
    width: 44;
    height: auto;
    border: round $primary;
    background: $surface;
    padding: 1 2;
}

.menu-panel .menu-title {
    text-align: center;
    text-style: bold;
    margin-bottom: 1;
}

.menu-panel ListView {
    height: auto;
    background: transparent;
    scrollbar-size: 0 0;
}

.menu-panel ListItem {
    padding: 0 1;
}

.menu-panel .menu-hint {
    color: $text-muted;
    text-align: center;
    margin-top: 1;
}

.filter-bar {
    height: auto;
    margin-bottom: 1;
}

.filter-bar Button {
    width: auto;
    min-width: 14;
    margin-right: 1;
}

.filter-bar Select {
    width: 26;
    margin-right: 1;
}
"""
