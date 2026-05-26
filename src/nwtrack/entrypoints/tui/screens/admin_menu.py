"""Admin sub-menu screen for the nwtrack TUI."""

from collections.abc import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService

_MENU_ITEMS = ["Institutions", "Tags", "Categories"]


class AdminMenuScreen(Screen):
    """Admin sub-menu — entry point for administrative CRUD workflows."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow

    def on_mount(self) -> None:
        self.sub_title = "Admin"

    def compose(self) -> ComposeResult:
        yield Header()
        items = [
            ListItem(Label(item), id=f"admin-{item.lower()}")
            for item in _MENU_ITEMS
        ]
        yield ListView(*items, id="admin-menu")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id == "admin-institutions":
            from nwtrack.entrypoints.tui.screens.institutions import (
                InstitutionsListScreen,
            )
            self.app.push_screen(InstitutionsListScreen(self._fetcher, self._uow))
        elif item_id == "admin-tags":
            from nwtrack.entrypoints.tui.screens.tags import TagsListScreen
            self.app.push_screen(TagsListScreen(self._fetcher, self._uow))
        elif item_id == "admin-categories":
            from nwtrack.entrypoints.tui.screens.categories import (
                CategoriesListScreen,
            )
            self.app.push_screen(CategoriesListScreen(self._fetcher, self._uow))
