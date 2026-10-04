"""Admin screen for choosing account display order and visibility."""

from collections.abc import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.infra.persistence.orm.models import Account


class AccountOrderScreen(Screen):
    """All accounts in display order; move the selected one or hide/unhide it."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("u", "move_up", "Move up"),
        Binding("d", "move_down", "Move down"),
        Binding("h", "toggle_hidden", "Hide/unhide"),
    ]

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow
        self._accounts: list[Account] = []

    def on_mount(self) -> None:
        self.sub_title = "Account Order"
        self._refresh_table()

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="order-table", zebra_stripes=True, cursor_type="row")
        yield Footer()

    def _refresh_table(self, cursor_account_id: int | None = None) -> None:
        table = self.query_one("#order-table", DataTable)
        table.clear(columns=True)
        table.add_columns("#", "Name", "Status", "Category", "Hidden")
        self._accounts = self._fetcher.get_accounts(
            active_only=False, include_hidden=True
        )
        for position, acc in enumerate(self._accounts, start=1):
            table.add_row(
                str(position),
                acc.name,
                acc.status.value,
                acc.category_name,
                "yes" if acc.is_hidden else "",
                key=str(acc.id),
            )
        if cursor_account_id is not None:
            for index, acc in enumerate(self._accounts):
                if acc.id == cursor_account_id:
                    table.move_cursor(row=index)
                    break

    def _selected(self) -> Account | None:
        row = self.query_one("#order-table", DataTable).cursor_row
        return self._accounts[row] if 0 <= row < len(self._accounts) else None

    def _move(self, direction: int) -> None:
        account = self._selected()
        if account is None:
            return
        with self._uow() as uow:
            moved = uow.accounts.move(account.id, direction)
        if moved:
            self._refresh_table(cursor_account_id=account.id)

    def action_move_up(self) -> None:
        self._move(-1)

    def action_move_down(self) -> None:
        self._move(1)

    def action_toggle_hidden(self) -> None:
        account = self._selected()
        if account is None:
            return
        with self._uow() as uow:
            uow.accounts.set_hidden(account.id, not account.is_hidden)
        self._refresh_table(cursor_account_id=account.id)
