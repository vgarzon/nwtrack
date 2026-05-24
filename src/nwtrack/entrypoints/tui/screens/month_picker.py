"""Month picker modal for the nwtrack TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label

from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.utils import months_to_grid


class MonthPickerModal(ModalScreen[Month | None]):
    """Overlay modal for selecting a balance month.

    Returns the selected Month on confirmation, or None on cancel.
    Only months that have at least one balance record are shown.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    MonthPickerModal {
        align: center middle;
    }
    #picker-container {
        width: 44;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #picker-title {
        text-align: center;
        margin-bottom: 1;
    }
    #month-grid {
        height: auto;
        grid-size: 3;
        grid-gutter: 1;
        margin-bottom: 1;
    }
    #month-grid Button {
        width: 10;
    }
    #month-grid Button.-selected-month {
        border: tall $accent;
    }
    """

    def __init__(
        self,
        current_month: Month,
        available_months: list[Month],
    ) -> None:
        super().__init__()
        self._current_month = current_month
        self._available_months = available_months

    def compose(self) -> ComposeResult:
        rows = months_to_grid(self._available_months, cols=3)
        with Vertical(id="picker-container"):
            yield Label("Select Month", id="picker-title")
            with Grid(id="month-grid"):
                for row in rows:
                    for month in row:
                        btn = Button(str(month), id=f"month-{month}")
                        if month == self._current_month:
                            btn.add_class("-selected-month")
                        yield btn
            yield Footer()

    def on_mount(self) -> None:
        # Focus the button for the current month if present; otherwise first button.
        try:
            self.query_one(f"#month-{self._current_month}", Button).focus()
        except Exception:
            buttons = self.query(Button)
            if buttons:
                buttons.first(Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("month-"):
            month_str = btn_id[len("month-"):]
            try:
                year, month_num = month_str.split("-")
                self.dismiss(Month(int(year), int(month_num)))
            except (ValueError, TypeError):
                self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
