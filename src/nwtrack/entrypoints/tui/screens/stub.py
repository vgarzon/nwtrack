"""Placeholder screen for TUI sections not yet implemented."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Label


class StubScreen(Screen):
    """Placeholder screen shown for menu items not yet implemented."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(self, section: str) -> None:
        super().__init__()
        self._section = section

    def on_mount(self) -> None:
        self.sub_title = self._section

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(f"{self._section} — not yet implemented", id="stub-label")
        yield Footer()
