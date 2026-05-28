"""Net worth history report screen for the nwtrack TUI."""

from collections.abc import Callable

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    HistoryAggregationRequest,
)
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.services.report_compatibility import to_networth_history
from nwtrack.application.use_cases.report_history_aggregation import (
    ReportHistoryAggregation,
)
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.screens.month_picker import MonthPickerModal

_CURRENCY = "USD"
_STATUS_SCOPE = AccountStatusScope.HISTORICAL
_DEFAULT_MONTHS = 12


class NetWorthHistoryScreen(Screen):
    """Scrollable net worth history report: assets, liabilities, net worth by month."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow
        self._start_month: Month | None = None
        self._end_month: Month | None = None
        self._available: list[Month] = []

    # ── Layout ──────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        yield Button("Start: —", id="btn-start")
        yield Button("End: —", id="btn-end")
        yield Label("", id="error-label")
        yield DataTable(id="history-table", zebra_stripes=True)
        yield Footer()

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        table = self.query_one("#history-table", DataTable)
        table.add_columns(
            "Month",
            Text("Assets", justify="right"),
            Text("Liabilities", justify="right"),
            Text("Net Worth", justify="right"),
        )

        self._available = self._fetcher.get_available_aggregation_months(
            AggregationDimension.SIDE,
            currency_code=_CURRENCY,
            status_scope=_STATUS_SCOPE,
        )
        if not self._available:
            self._show_error("No net worth data found in USD.")
            return

        self._end_month = self._available[-1]
        start_idx = max(0, len(self._available) - _DEFAULT_MONTHS)
        self._start_month = self._available[start_idx]
        self._update_buttons()
        self._refresh_table()

    # ── Actions ──────────────────────────────────────────────────────────────

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

    def _update_buttons(self) -> None:
        self.query_one("#btn-start", Button).label = (
            f"Start: {self._start_month}" if self._start_month else "Start: —"
        )
        self.query_one("#btn-end", Button).label = (
            f"End: {self._end_month}" if self._end_month else "End: —"
        )
        if self._start_month and self._end_month:
            self.sub_title = f"{self._start_month} → {self._end_month} ({_CURRENCY})"

    def _refresh_table(self) -> None:
        if self._start_month is None or self._end_month is None:
            return

        table = self.query_one("#history-table", DataTable)
        table.clear()

        if self._end_month < self._start_month:
            self._show_error("End month must be on or after start month.")
            return

        use_case = ReportHistoryAggregation(uow=self._uow)
        result = use_case.run(
            HistoryAggregationRequest(
                start_month=self._start_month,
                end_month=self._end_month,
                dimension=AggregationDimension.SIDE,
                currency_code=_CURRENCY,
                status_scope=_STATUS_SCOPE,
            )
        )

        if not result.success or result.data is None:
            self._show_error(result.error_message or "Failed to load report.")
            return

        nws = to_networth_history(result.data)
        nws.sort(key=lambda x: x.month)

        self._hide_error()
        for nw in nws:
            table.add_row(
                str(nw.month),
                Text(f"{nw.assets:,}", justify="right"),
                Text(f"{nw.liabilities:,}", justify="right"),
                Text(f"{nw.net_worth:,}", justify="right"),
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
