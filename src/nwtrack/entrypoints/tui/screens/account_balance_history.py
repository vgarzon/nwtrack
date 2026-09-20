"""Single-account balance history report screen for the nwtrack TUI."""

from collections.abc import Callable

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    Select,
)

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.report_account_history import (
    ReportAccountBalanceHistory,
)
from nwtrack.domain.models import Account
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.screens.month_picker import MonthPickerModal

_DEFAULT_MONTHS = 12


class AccountBalanceHistoryScreen(Screen):
    """Scrollable single-account balance history report: month, balance, delta."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow
        self._accounts: list[Account] = []
        self._account_id: int | None = None
        self._start_month: Month | None = None
        self._end_month: Month | None = None
        self._available: list[Month] = []

    # ── Layout ──────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        self._accounts = self._fetcher.get_accounts(active_only=False)
        account_options = [(a.name, str(a.id)) for a in self._accounts]
        yield Select(
            options=account_options,
            prompt="Select account",
            id="account-select",
        )
        yield Button("Start: —", id="btn-start")
        yield Button("End: —", id="btn-end")
        yield Label("", id="error-label", classes="error-text")
        yield DataTable(id="history-table", zebra_stripes=True)
        yield Label("", id="summary-label")
        yield Footer()

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        table = self.query_one("#history-table", DataTable)
        table.add_columns(
            "Month",
            Text("Balance", justify="right"),
            Text("Delta", justify="right"),
        )

        if not self._accounts:
            self._show_error("No accounts found.")
            return

        self._account_id = self._accounts[0].id
        self.query_one("#account-select", Select).value = str(self._account_id)
        self._load_account_months()

    # ── Actions ──────────────────────────────────────────────────────────────

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "account-select":
            return
        if event.value is Select.NULL:
            return
        self._account_id = int(str(event.value))
        self._start_month = None
        self._end_month = None
        self._load_account_months()

    @work
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self._available:
            return
        current = (
            self._start_month if event.button.id == "btn-start" else self._end_month
        ) or self._available[-1]
        result: Month | None = await self.app.push_screen_wait(
            MonthPickerModal(current, self._available)
        )
        if result is None:
            return
        if event.button.id == "btn-start":
            self._start_month = result
        else:
            self._end_month = result
        self._update_buttons()
        self._refresh_table()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _load_account_months(self) -> None:
        if self._account_id is None:
            return
        balances = self._fetcher.get_balances_for_account(self._account_id)
        self._available = sorted({balance.month for balance in balances})

        self.query_one("#history-table", DataTable).clear()
        self.query_one("#summary-label", Label).update("")

        if not self._available:
            self._start_month = None
            self._end_month = None
            self._update_buttons()
            self._show_error("No balance records found for this account.")
            return

        self._hide_error()
        self._end_month = self._available[-1]
        start_idx = max(0, len(self._available) - _DEFAULT_MONTHS)
        self._start_month = self._available[start_idx]
        self._update_buttons()
        self._refresh_table()

    def _update_buttons(self) -> None:
        self.query_one("#btn-start", Button).label = (
            f"Start: {self._start_month}" if self._start_month else "Start: —"
        )
        self.query_one("#btn-end", Button).label = (
            f"End: {self._end_month}" if self._end_month else "End: —"
        )
        if self._start_month and self._end_month:
            account = next(
                (a for a in self._accounts if a.id == self._account_id), None
            )
            name = account.name if account else "?"
            self.sub_title = f"{name} | {self._start_month} → {self._end_month}"

    def _refresh_table(self) -> None:
        if (
            self._account_id is None
            or self._start_month is None
            or self._end_month is None
        ):
            return

        table = self.query_one("#history-table", DataTable)
        table.clear()
        summary_label = self.query_one("#summary-label", Label)

        if self._end_month < self._start_month:
            self._show_error("End month must be on or after start month.")
            return

        use_case = ReportAccountBalanceHistory(uow=self._uow)
        result = use_case.run(self._account_id, self._start_month, self._end_month)

        if not result.success or result.data is None:
            self._show_error(result.error_message or "Failed to load report.")
            return

        self._hide_error()
        data = result.data
        for row in data.rows:
            if row.balance is None:
                table.add_row(str(row.month), Text("—", justify="right"), "")
                continue
            balance_cell = Text(f"{row.balance:,}", justify="right")
            if row.delta is None:
                delta_cell: Text | str = ""
            else:
                sign = "+" if row.delta >= 0 else ""
                delta_cell = Text(f"{sign}{row.delta:,}", justify="right")
            table.add_row(str(row.month), balance_cell, delta_cell)

        if data.summary is None:
            summary_label.update("No balance records in selected range.")
        else:
            summary = data.summary
            sign = "+" if summary.total_change >= 0 else ""
            summary_label.update(
                f"Min: {summary.min_balance:,}  Max: {summary.max_balance:,}  "
                f"Avg: {summary.average_balance:,.2f}  "
                f"Total change: {sign}{summary.total_change:,} "
                f"({summary.first_month} → {summary.last_month})"
            )

    def _show_error(self, message: str) -> None:
        label = self.query_one("#error-label", Label)
        label.update(message)
        label.display = True
        self.query_one("#history-table", DataTable).clear()

    def _hide_error(self) -> None:
        label = self.query_one("#error-label", Label)
        label.update("")
        label.display = False
