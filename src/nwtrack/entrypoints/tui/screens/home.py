"""Home screen for the nwtrack TUI."""

from collections.abc import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService

_MENU_ITEMS = ["Balances", "Reports", "Accounts", "Admin"]


class HomeScreen(Screen):
    """Main menu screen — entry point of the TUI."""

    BINDINGS = [Binding("escape,q", "app.quit", "Quit")]

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow

    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(
            *[ListItem(Label(item), id=f"menu-{item.lower()}") for item in _MENU_ITEMS],
            id="home-menu",
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        label = event.item.id or ""
        section = label.removeprefix("menu-").capitalize()
        if section == "Balances":
            from nwtrack.entrypoints.tui.screens.balance_update import (
                BalanceUpdateScreen,
            )
            self.app.push_screen(BalanceUpdateScreen(self._fetcher, self._uow))
        elif section == "Reports":
            from nwtrack.entrypoints.tui.screens.reports_menu import ReportsMenuScreen
            self.app.push_screen(ReportsMenuScreen(self._fetcher, self._uow))
        elif section == "Accounts":
            from nwtrack.entrypoints.tui.screens.accounts import AccountsListScreen
            self.app.push_screen(AccountsListScreen(self._fetcher, self._uow))
        elif section == "Admin":
            from nwtrack.entrypoints.tui.screens.admin_menu import AdminMenuScreen
            self.app.push_screen(AdminMenuScreen(self._fetcher, self._uow))
