"""
Textual TUI application for nwtrack.
"""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header


class NWTrackApp(App):
    """nwtrack Textual application."""

    TITLE = "nwtrack"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
