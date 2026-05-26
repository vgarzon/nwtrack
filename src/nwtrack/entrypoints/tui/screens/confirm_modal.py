"""Generic confirmation modal for destructive actions."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label


class ConfirmModal(ModalScreen[bool]):
    """Overlay confirmation dialog.

    Returns True on confirm, False on cancel.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    ConfirmModal {
        align: center middle;
    }
    #confirm-container {
        width: 54;
        height: auto;
        border: thick $warning;
        background: $surface;
        padding: 1 2;
    }
    #confirm-message {
        margin-bottom: 1;
    }
    #confirm-buttons {
        margin-top: 1;
        align: right middle;
        height: auto;
    }
    #confirm-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(
        self,
        message: str,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
    ) -> None:
        super().__init__()
        self._message = message
        self._confirm_label = confirm_label
        self._cancel_label = cancel_label

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-container"):
            yield Label(self._message, id="confirm-message")
            with Horizontal(id="confirm-buttons"):
                yield Button(self._cancel_label, id="btn-cancel", variant="default")
                yield Button(self._confirm_label, id="btn-confirm", variant="warning")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#btn-confirm", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-confirm")

    def action_cancel(self) -> None:
        self.dismiss(False)
