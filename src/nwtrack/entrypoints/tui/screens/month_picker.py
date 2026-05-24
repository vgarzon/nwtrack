"""Month picker modal for the nwtrack TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Label

from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.utils import months_to_grid


class MonthPickerModal(ModalScreen[Month | None]):
    """Overlay modal for selecting a balance month.

    Returns the selected Month on confirmation, or None on cancel.
    Only months that have at least one balance record are shown.
    Arrow keys navigate the grid; Enter confirms; Escape cancels.
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
    #month-table {
        height: auto;
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        current_month: Month,
        available_months: list[Month],
    ) -> None:
        super().__init__()
        self._current_month = current_month
        self._grid = months_to_grid(available_months, cols=3)

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-container"):
            yield Label("Select Month", id="picker-title")
            yield DataTable(
                id="month-table",
                cursor_type="cell",
                show_header=False,
                zebra_stripes=False,
            )
            yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#month-table", DataTable)
        table.add_columns("", "", "")

        cursor_row, cursor_col = 0, 0
        for row_idx, row in enumerate(self._grid):
            padded = row + [None] * (3 - len(row))
            table.add_row(*[str(m) if m else "" for m in padded])
            for col_idx, month in enumerate(row):
                if month == self._current_month:
                    cursor_row, cursor_col = row_idx, col_idx

        table.move_cursor(row=cursor_row, column=cursor_col)
        table.focus()

    def on_data_table_cell_selected(
        self, event: DataTable.CellSelected
    ) -> None:
        row_idx = event.coordinate.row
        col_idx = event.coordinate.column
        if row_idx < len(self._grid) and col_idx < len(self._grid[row_idx]):
            self.dismiss(self._grid[row_idx][col_idx])

    def action_cancel(self) -> None:
        self.dismiss(None)
