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
"""
