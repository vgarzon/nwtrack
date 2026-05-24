"""
Balance update screen for the nwtrack TUI.

The screen owns the full balance update workflow directly — it calls FetchService
and UnitOfWork rather than driving BalanceUpdater.run() through a presenter adapter.
See specs/260523-tui-step2-textual-balance-prototype/requirements.md (Findings) for
why the adapter-swap pattern is not viable here.
"""

from collections.abc import Callable
from decimal import Decimal, InvalidOperation

from textual.app import ComposeResult
from textual.coordinate import Coordinate
from textual.events import Key
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Label

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Balance
from nwtrack.domain.value_objects import Month


class BalanceUpdateScreen(Screen):
    """Editable grid of account balances for the most recent month."""

    BINDINGS = [("escape,q", "app.quit", "Quit")]

    net_worth: reactive[int] = reactive(0)

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow
        self._month: Month | None = None
        self._balances: list[Balance] = []
        self._editing_row: int | None = None

    # ── Layout ──────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("", id="month-label")
        yield DataTable(id="balance-table", zebra_stripes=True, cursor_type="row")
        yield Input(placeholder="New amount", id="balance-input")
        yield Label("", id="networth-label")
        yield Footer()

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self.query_one("#balance-input", Input).display = False
        self._load_data()

    def _load_data(self) -> None:
        recent = self._fetcher.get_recent_months(n_months=1)
        if not recent:
            self.query_one("#month-label", Label).update(
                "No balance data found. Run `nwtrack balances update` first."
            )
            return

        self._month = recent[0]
        self.title = f"nwtrack — {self._month}"
        self.query_one("#month-label", Label).update(
            f"Editing: [bold]{self._month}[/bold]"
        )
        self._refresh_table()
        self._refresh_networth()

    def _refresh_table(self) -> None:
        if self._month is None:
            return
        table = self.query_one("#balance-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Account", "Category", "Currency", "Amount")

        self._balances = self._fetcher.get_month_balances(
            self._month, active_only=True
        )
        for balance in self._balances:
            amount_display = self._format_amount(balance.amount)
            table.add_row(
                balance.account.name,
                balance.account.category.name,
                balance.account.currency_code,
                amount_display,
                key=str(balance.account.id),
            )

    def _refresh_networth(self) -> None:
        if self._month is None:
            return
        nw = self._fetcher.get_networth(self._month, "USD")
        label = self.query_one("#networth-label", Label)
        if nw is not None:
            amount = self._format_amount(nw.net_worth)
            label.update(f"Net worth ({self._month}): [bold]{amount}[/bold] USD")
        else:
            label.update("")

    # ── Event handlers ───────────────────────────────────────────────────────

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if not self._balances:
            return

        row_idx = event.cursor_row
        if row_idx >= len(self._balances):
            return

        self._editing_row = row_idx
        balance = self._balances[row_idx]
        current = self._format_amount(balance.amount)

        inp = self.query_one("#balance-input", Input)
        inp.value = current
        inp.display = True
        inp.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self._editing_row is None or self._month is None:
            return

        raw = event.value.strip().replace(",", "")
        try:
            amount = int(Decimal(raw))
        except (InvalidOperation, ValueError):
            event.input.display = False
            self._editing_row = None
            return

        balance = self._balances[self._editing_row]
        account_id = balance.account.id

        with self._uow() as uow:
            uow.balances.update(
                account_id=account_id, month=self._month, new_amount=amount
            )

        # Refresh only the edited row
        table = self.query_one("#balance-table", DataTable)
        table.update_cell_at(
            Coordinate(self._editing_row, 3),
            self._format_amount(amount),
            update_width=True,
        )
        # Also update the in-memory balance so net worth recalc is accurate
        self._balances[self._editing_row] = self._fetcher.get_balance_for_account_id(
            self._month, account_id
        )

        self._refresh_networth()

        event.input.display = False
        self._editing_row = None
        table.focus()

    def on_key(self, event: Key) -> None:
        inp = self.query_one("#balance-input", Input)
        if event.key == "escape" and inp.display:
            inp.display = False
            self._editing_row = None
            self.query_one("#balance-table", DataTable).focus()
            event.stop()

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _format_amount(amount: int) -> str:
        return f"{amount:,}"
