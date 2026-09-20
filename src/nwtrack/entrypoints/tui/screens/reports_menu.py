"""Reports sub-menu screen for the nwtrack TUI."""

from collections.abc import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService

_MENU_ITEMS = ["Net Worth History", "Aggregation", "Account History"]


class ReportsMenuScreen(Screen):
    """Reports sub-menu — entry point for TUI report workflows."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
    ) -> None:
        super().__init__(classes="menu-screen")
        self._fetcher = fetcher
        self._uow = uow

    def on_mount(self) -> None:
        self.sub_title = "Reports"

    def compose(self) -> ComposeResult:
        yield Header()
        items = [
            ListItem(Label(item), id=f"report-{item.lower().replace(' ', '-')}")
            for item in _MENU_ITEMS
        ]
        with Vertical(id="reports-menu-panel", classes="menu-panel"):
            yield Label("Reports", classes="menu-title")
            yield ListView(*items, id="reports-menu")
            yield Label("Esc back", classes="menu-hint")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id == "report-net-worth-history":
            from nwtrack.entrypoints.tui.screens.networth_history import (
                NetWorthHistoryScreen,
            )

            self.app.push_screen(NetWorthHistoryScreen(self._fetcher, self._uow))
        elif item_id == "report-aggregation":
            from nwtrack.entrypoints.tui.screens.aggregation import AggregationScreen

            self.app.push_screen(AggregationScreen(self._fetcher, self._uow))
        elif item_id == "report-account-history":
            from nwtrack.entrypoints.tui.screens.account_balance_history import (
                AccountBalanceHistoryScreen,
            )

            self.app.push_screen(AccountBalanceHistoryScreen(self._fetcher, self._uow))
