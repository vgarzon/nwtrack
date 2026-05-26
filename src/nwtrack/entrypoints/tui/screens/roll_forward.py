"""Roll-forward modal for the nwtrack TUI."""

from collections.abc import Callable

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.screens.month_picker import MonthPickerModal


class RollForwardModal(ModalScreen[Month | None]):
    """Overlay modal for rolling balances forward to the next month.

    Source month defaults to the month passed in, but can be changed.
    Target month is always the next calendar month after the latest month
    that has any balance records.

    Dismisses with the target Month on success, None on cancel.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "confirm", "Confirm"),
        Binding("m", "pick_source", "Change source"),
    ]

    DEFAULT_CSS = """
    RollForwardModal {
        align: center middle;
    }
    #rf-container {
        width: 56;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #rf-title {
        text-align: center;
        margin-bottom: 1;
    }
    #rf-warning {
        color: $warning;
        margin-top: 1;
    }
    #rf-error {
        color: $error;
        margin-top: 1;
    }
    #rf-hint {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
        source_month: Month,
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow
        self._source_month = source_month
        self._target_month: Month | None = None
        self._target_has_balances = False

    def compose(self) -> ComposeResult:
        with Vertical(id="rf-container"):
            yield Label("Roll Balances Forward", id="rf-title")
            yield Label("", id="rf-source")
            yield Label("", id="rf-target")
            yield Label("", id="rf-warning")
            yield Label("", id="rf-error")
            yield Label("Ctrl+S to confirm  ·  M to change source", id="rf-hint")
            yield Footer()

    def on_mount(self) -> None:
        self._compute_target()
        self._update_labels()

    def _compute_target(self) -> None:
        recent = self._fetcher.get_recent_months(n_months=1)
        if recent:
            self._target_month = recent[0].increment()
            self._target_has_balances = self._fetcher.check_month_in_balances(
                self._target_month
            )
        else:
            self._target_month = None
            self._target_has_balances = False

    def _update_labels(self) -> None:
        self.query_one("#rf-source", Label).update(
            f"Source:  [bold]{self._source_month}[/bold]"
        )
        if self._target_month:
            self.query_one("#rf-target", Label).update(
                f"Target:  [bold]{self._target_month}[/bold]"
            )
        else:
            self.query_one("#rf-target", Label).update(
                "Target:  (no balance data found)"
            )
        if self._target_has_balances:
            self.query_one("#rf-warning", Label).update(
                f"{self._target_month} already has balances — cannot overwrite."
            )
        else:
            self.query_one("#rf-warning", Label).update("")
        self.query_one("#rf-error", Label).update("")

    @work
    async def action_pick_source(self) -> None:
        available = self._fetcher.get_recent_months(n_months=120)
        result: Month | None = await self.app.push_screen_wait(
            MonthPickerModal(self._source_month, available)
        )
        if result is not None:
            self._source_month = result
            self._update_labels()

    def action_confirm(self) -> None:
        error = self.query_one("#rf-error", Label)
        if self._target_month is None:
            error.update("No balance data found — nothing to roll forward.")
            return
        if self._target_has_balances:
            error.update(
                f"{self._target_month} already has balances — cannot overwrite."
            )
            return
        if not self._fetcher.check_month_in_balances(self._source_month):
            error.update(f"No balances found for {self._source_month}.")
            return
        try:
            with self._uow() as uow:
                count = uow.balances.copy_by_month(
                    self._source_month, self._target_month
                )
                if count == 0:
                    uow.rollback()
                    error.update("No balances were copied.")
                    return
        except Exception:
            error.update("Failed to copy balances.")
            return
        self.dismiss(self._target_month)

    def action_cancel(self) -> None:
        self.dismiss(None)
