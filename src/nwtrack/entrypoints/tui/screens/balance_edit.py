"""Balance edit modal for the nwtrack TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label

from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.utils import parse_amount_input


class BalanceEditModal(ModalScreen[int | None]):
    """Overlay modal for editing a single account balance.

    Returns the new amount in cents on confirmation, or None on cancel.
    Shows an inline error message on invalid input without dismissing.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    BalanceEditModal {
        align: center middle;
    }
    #edit-container {
        width: 44;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #edit-title {
        text-align: center;
        margin-bottom: 1;
    }
    #edit-error {
        color: $error;
        margin-top: 1;
    }
    #edit-buttons {
        margin-top: 1;
        align: right middle;
        height: auto;
    }
    """

    def __init__(
        self,
        account_name: str,
        month: Month,
        current_amount_cents: int,
    ) -> None:
        super().__init__()
        self._account_name = account_name
        self._month = month
        self._current_amount_cents = current_amount_cents

    def compose(self) -> ComposeResult:
        current_display = f"${self._current_amount_cents / 100:,.2f}"
        with Vertical(id="edit-container"):
            yield Label("Edit Balance", id="edit-title")
            yield Label(f"Account:  {self._account_name}")
            yield Label(f"Month:    {self._month}")
            yield Label(f"Current:  {current_display}")
            yield Input(placeholder="New amount", id="edit-input")
            yield Label("", id="edit-error")
            with Vertical(id="edit-buttons"):
                yield Footer()

    def on_mount(self) -> None:
        self.query_one("#edit-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip().replace(",", "")
        try:
            cents = parse_amount_input(raw)
        except ValueError:
            self.query_one("#edit-error", Label).update("Enter a positive number")
            return
        self.query_one("#edit-error", Label).update("")
        self.dismiss(cents)

    def action_cancel(self) -> None:
        self.dismiss(None)
