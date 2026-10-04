"""
Balance update screen for the nwtrack TUI.

The screen owns the full balance update workflow directly — it calls FetchService
and UnitOfWork rather than driving BalanceUpdater.run() through a presenter adapter.
See specs/260523-phase-25-tui-textual-balance-prototype/requirements.md (Findings) for
why the adapter-swap pattern is not viable here.
"""

from collections.abc import Callable

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.balance_change_check import evaluate_balance_change
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Balance, Side
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.screens.balance_edit import BalanceEditModal
from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal
from nwtrack.entrypoints.tui.screens.month_picker import MonthPickerModal
from nwtrack.entrypoints.tui.screens.roll_forward import RollForwardModal
from nwtrack.entrypoints.tui.screens.transfer import TransferModal


class BalanceUpdateScreen(Screen):
    """Editable grid of account balances for a selected month."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("m", "pick_month", "Change month"),
        Binding("r", "roll_forward", "Roll forward"),
        Binding("t", "transfer", "Transfer"),
        Binding("h", "toggle_hidden", "Show/hide hidden"),
    ]

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
        change_warning_threshold_pct: float = 20.0,
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow
        self._change_warning_threshold_pct = change_warning_threshold_pct
        self._month: Month | None = None
        self._balances: list[Balance] = []
        self._show_hidden = False

    # ── Layout ──────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="balance-table", zebra_stripes=True, cursor_type="row")
        yield Label("", id="networth-label")
        yield Label("", id="visible-total-label")
        yield Footer()

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self._load_data()

    def _load_data(self) -> None:
        recent = self._fetcher.get_recent_months(n_months=1)
        if not recent:
            self.sub_title = (
                "No balance data found — run `nwtrack balances update` first."
            )
            return

        self._month = recent[0]
        self._update_header()
        self._refresh_table()
        self._refresh_networth()

    def _update_header(self) -> None:
        self.sub_title = f"Update Balances — {self._month}" if self._month else ""

    def _refresh_table(self) -> None:
        if self._month is None:
            return
        table = self.query_one("#balance-table", DataTable)
        table.clear(columns=True)
        table.add_columns(
            "Institution",
            "Account",
            "Category",
            "Side",
            Text("Amount", justify="right"),
        )

        self._balances = self._fetcher.get_month_balances(
            self._month, active_only=True, include_hidden=self._show_hidden
        )
        for balance in self._balances:
            institution = (
                balance.account.institution.name if balance.account.institution else ""
            )
            table.add_row(
                institution,
                balance.account.name,
                balance.account.category.name,
                balance.account.category.side.value,
                Text(self._format_amount(balance.amount), justify="right"),
                key=str(balance.account.id),
            )

    def _refresh_visible_total(self) -> None:
        """Per-currency sum of the shown rows, liabilities counted negative."""
        totals: dict[str, int] = {}
        for balance in self._balances:
            account = balance.account
            sign = -1 if account.category.side == Side.LIABILITY else 1
            totals[account.currency_code] = (
                totals.get(account.currency_code, 0) + sign * balance.amount
            )
        label = self.query_one("#visible-total-label", Label)
        if not totals:
            label.update("")
            return
        parts = "  ".join(
            f"[bold]{self._format_amount(amount)}[/bold] {currency}"
            for currency, amount in sorted(totals.items())
        )
        suffix = " (incl. hidden)" if self._show_hidden else ""
        label.update(f"Visible rows{suffix}: {parts}")

    def _refresh_networth(self) -> None:
        if self._month is None:
            return
        self._refresh_visible_total()
        nw = self._fetcher.get_networth(self._month, "USD")
        label = self.query_one("#networth-label", Label)
        if nw is not None:
            amount = self._format_amount(nw.net_worth)
            label.update(f"Net worth ({self._month}): [bold]{amount}[/bold] USD")
        else:
            label.update("")

    # ── Actions ──────────────────────────────────────────────────────────────

    @work
    async def action_pick_month(self) -> None:
        if self._month is None:
            return
        available = self._fetcher.get_recent_months(n_months=120)
        result: Month | None = await self.app.push_screen_wait(
            MonthPickerModal(self._month, available)
        )
        if result is not None and result != self._month:
            self._month = result
            self._update_header()
            self._refresh_table()
            self._refresh_networth()

    # ── Event handlers ───────────────────────────────────────────────────────

    @work
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if not self._balances or self._month is None:
            return

        row_idx = event.cursor_row
        if row_idx >= len(self._balances):
            return

        balance = self._balances[row_idx]
        current_amount = balance.amount
        result: int | None = None
        while True:
            result = await self.app.push_screen_wait(
                BalanceEditModal(
                    account_name=balance.account.name,
                    month=self._month,
                    current_amount=current_amount,
                )
            )
            if result is None:
                return

            warning = evaluate_balance_change(
                balance.amount, result, self._change_warning_threshold_pct
            )
            if warning is None:
                break

            direction = "above" if warning.increased else "below"
            confirmed = await self.app.push_screen_wait(
                ConfirmModal(
                    f"The value you entered is {warning.pct_change:.1f}% {direction} "
                    f"the current balance ({balance.amount:,} → {result:,}). "
                    "Do you want to proceed?"
                )
            )
            if confirmed:
                break
            # Declined: reopen the edit modal with the same prior amount
            current_amount = balance.amount

        account_id = balance.account.id
        with self._uow() as uow:
            uow.balances.update(
                account_id=account_id, month=self._month, new_amount=result
            )

        table = self.query_one("#balance-table", DataTable)
        table.update_cell_at(
            Coordinate(row_idx, 4),
            Text(self._format_amount(result), justify="right"),
            update_width=True,
        )
        self._balances[row_idx] = self._fetcher.get_balance_for_account_id(
            self._month, account_id
        )
        self._refresh_networth()

    def action_toggle_hidden(self) -> None:
        self._show_hidden = not self._show_hidden
        self._refresh_table()
        self._refresh_networth()
        self.notify(
            "Showing hidden accounts" if self._show_hidden else "Hiding hidden accounts"
        )

    @work
    async def action_roll_forward(self) -> None:
        if self._month is None:
            return
        result: Month | None = await self.app.push_screen_wait(
            RollForwardModal(
                fetcher=self._fetcher,
                uow=self._uow,
                source_month=self._month,
            )
        )
        if result is not None:
            self._month = result
            self._update_header()
            self.call_after_refresh(self._refresh_table)
            self.call_after_refresh(self._refresh_networth)

    @work
    async def action_transfer(self) -> None:
        if self._month is None:
            return
        row_idx = self.query_one("#balance-table", DataTable).cursor_row
        from_account_id = (
            self._balances[row_idx].account.id
            if 0 <= row_idx < len(self._balances)
            else None
        )
        await self.app.push_screen_wait(
            TransferModal(
                fetcher=self._fetcher,
                uow=self._uow,
                month=self._month,
                from_account_id=from_account_id,
            )
        )
        self.call_after_refresh(self._refresh_table)
        self.call_after_refresh(self._refresh_networth)

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _format_amount(amount: int) -> str:
        return f"{amount:,}"
