"""Single-month aggregation report screen for the nwtrack TUI."""

from collections.abc import Callable

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, Select

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    SingleMonthAggregationRequest,
)
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.report_single_month_aggregation import (
    ReportSingleMonthAggregation,
)
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.screens.month_picker import MonthPickerModal

_DEFAULT_DIMENSION = AggregationDimension.CATEGORY
_STATUS_SCOPE = AccountStatusScope.ACTIVE

_DIMENSION_OPTIONS: list[tuple[str, AggregationDimension]] = [
    ("Category", AggregationDimension.CATEGORY),
    ("Side", AggregationDimension.SIDE),
    ("Institution", AggregationDimension.INSTITUTION),
    ("Currency", AggregationDimension.CURRENCY),
    ("Tag", AggregationDimension.TAG),
]


class AggregationScreen(Screen):
    """Grouped balance totals for one month, by a user-selected dimension."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow
        self._month: Month | None = None
        self._dimension: AggregationDimension = _DEFAULT_DIMENSION
        self._available: list[Month] = []

    # ── Layout ──────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        yield Button("Month: —", id="btn-month")
        yield Select(
            options=[(label, dim) for label, dim in _DIMENSION_OPTIONS],
            value=_DEFAULT_DIMENSION,
            id="dim-select",
        )
        yield Label("", id="error-label")
        yield DataTable(id="agg-table", zebra_stripes=True)
        yield Footer()

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        table = self.query_one("#agg-table", DataTable)
        table.add_columns("Group", Text("Amount", justify="right"))

        self._available = self._fetcher.get_available_aggregation_months(
            _DEFAULT_DIMENSION,
            currency_code=None,
            status_scope=_STATUS_SCOPE,
        )
        if not self._available:
            self._show_error("No balance data found.")
            return

        self._month = self._available[-1]
        self._update_button()
        self._refresh_table()

    # ── Actions ──────────────────────────────────────────────────────────────

    @work
    async def on_button_pressed(self, _event: Button.Pressed) -> None:
        if not self._available or self._month is None:
            return
        result: Month | None = await self.app.push_screen_wait(
            MonthPickerModal(self._month, self._available)
        )
        if result is not None and result != self._month:
            self._month = result
            self._update_button()
            self._refresh_table()

    def on_select_changed(self, event: Select.Changed) -> None:
        if isinstance(event.value, AggregationDimension):
            self._dimension = event.value
            self._refresh_table()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _update_button(self) -> None:
        self.query_one("#btn-month", Button).label = (
            f"Month: {self._month}" if self._month else "Month: —"
        )

    def _update_subtitle(self) -> None:
        dim_label = next(
            (label for label, dim in _DIMENSION_OPTIONS if dim == self._dimension),
            self._dimension.value.capitalize(),
        )
        self.sub_title = (
            f"{self._month} — by {dim_label}" if self._month else "Aggregation"
        )

    def _refresh_table(self) -> None:
        if self._month is None:
            return

        table = self.query_one("#agg-table", DataTable)
        table.clear(columns=True)

        group_label = next(
            (label for label, dim in _DIMENSION_OPTIONS if dim == self._dimension),
            "Group",
        )
        table.add_columns(group_label, Text("Amount", justify="right"))

        use_case = ReportSingleMonthAggregation(uow=self._uow)
        result = use_case.run(
            SingleMonthAggregationRequest(
                month=self._month,
                dimension=self._dimension,
                currency_code=None,
                status_scope=_STATUS_SCOPE,
            )
        )

        if not result.success or result.data is None:
            self._show_error(result.error_message or "Failed to load report.")
            self._update_subtitle()
            return

        self._hide_error()
        self._update_subtitle()
        for group in result.data.groups:
            table.add_row(group.label, Text(f"{group.amount:,}", justify="right"))

    def _show_error(self, message: str) -> None:
        label = self.query_one("#error-label", Label)
        label.update(message)
        label.display = True
        self.query_one("#agg-table", DataTable).clear()

    def _hide_error(self) -> None:
        label = self.query_one("#error-label", Label)
        label.update("")
        label.display = False
