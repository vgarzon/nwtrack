"""
Textual TUI application for nwtrack.
"""

from collections.abc import Callable

from textual.app import App

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.entrypoints.tui.screens.home import HomeScreen


class NWTrackApp(App):
    """nwtrack Textual application."""

    TITLE = "nwtrack"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow

    def on_mount(self) -> None:
        self.push_screen(HomeScreen(self._fetcher, self._uow))
