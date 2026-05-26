"""Transfer balance modal for the nwtrack TUI."""

from collections.abc import Callable

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label, Select

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Balance, Side
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.screens.month_picker import MonthPickerModal
from nwtrack.entrypoints.tui.utils import parse_amount_input


class TransferModal(ModalScreen[bool]):
    """Overlay modal for transferring an amount between two accounts.

    Collects month, from-account, to-account, and amount.
    Handles asset/liability side semantics when computing balance deltas.
    Missing balances for the selected month are treated as zero.

    Dismisses with True on success, False on cancel.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Execute"),
        Binding("m", "pick_month", "Change month"),
    ]

    DEFAULT_CSS = """
    TransferModal {
        align: center middle;
    }
    #tr-container {
        width: 64;
        height: auto;
        max-height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
        overflow-y: auto;
    }
    #tr-title {
        text-align: center;
        margin-bottom: 1;
    }
    #tr-preview {
        margin-top: 1;
    }
    #tr-error {
        color: $error;
        margin-top: 1;
    }
    #tr-hint {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
        month: Month,
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow
        self._month = month
        self._accounts: list[Account] = []

    def compose(self) -> ComposeResult:
        self._accounts = self._fetcher.get_accounts(active_only=True)
        account_options = [(a.name, str(a.id)) for a in self._accounts]

        with Vertical(id="tr-container"):
            yield Label("Transfer Balance", id="tr-title")
            yield Label(f"Month: [bold]{self._month}[/bold]", id="tr-month")
            yield Label("From Account")
            yield Select(
                options=account_options,
                prompt="Select from account",
                id="select-from",
            )
            yield Label("To Account")
            yield Select(
                options=account_options,
                prompt="Select to account",
                id="select-to",
            )
            yield Label("Amount")
            yield Input(placeholder="Amount", id="input-amount")
            yield Label("", id="tr-preview")
            yield Label("", id="tr-error")
            yield Label("Ctrl+S to execute  ·  M to change month", id="tr-hint")
            yield Footer()

    def on_mount(self) -> None:
        self.query_one("#select-from", Select).focus()

    @work
    async def action_pick_month(self) -> None:
        available = self._fetcher.get_recent_months(n_months=120)
        result: Month | None = await self.app.push_screen_wait(
            MonthPickerModal(self._month, available)
        )
        if result is not None and result != self._month:
            self._month = result
            self.query_one("#tr-month", Label).update(
                f"Month: [bold]{self._month}[/bold]"
            )

    def action_submit(self) -> None:
        self._submit()

    def _submit(self) -> None:
        from_select = self.query_one("#select-from", Select)
        to_select = self.query_one("#select-to", Select)
        amount_input = self.query_one("#input-amount", Input)
        error = self.query_one("#tr-error", Label)
        preview = self.query_one("#tr-preview", Label)

        if from_select.value is Select.NULL:
            error.update("From account is required")
            from_select.focus()
            return
        if to_select.value is Select.NULL:
            error.update("To account is required")
            to_select.focus()
            return

        from_id = int(str(from_select.value))
        to_id = int(str(to_select.value))

        if from_id == to_id:
            error.update("From and To accounts must differ")
            return

        raw = amount_input.value.strip().replace(",", "")
        try:
            amount = parse_amount_input(raw)
        except ValueError:
            error.update("Enter a positive amount")
            amount_input.focus()
            return
        if amount == 0:
            error.update("Amount must be greater than zero")
            amount_input.focus()
            return

        from_account = next((a for a in self._accounts if a.id == from_id), None)
        to_account = next((a for a in self._accounts if a.id == to_id), None)
        if from_account is None or to_account is None:
            error.update("Account not found")
            return

        from_delta, to_delta = _compute_deltas(from_account, to_account, amount)

        preview.update(
            f"[bold]{from_account.name}[/bold]: {from_delta:+,}\n"
            f"[bold]{to_account.name}[/bold]: {to_delta:+,}"
        )
        error.update("")

        try:
            with self._uow() as uow:
                for account_id, delta in ((from_id, from_delta), (to_id, to_delta)):
                    try:
                        bal = uow.balances.get_by_account_id(self._month, account_id)
                        uow.balances.update(account_id, self._month, bal.amount + delta)
                    except IndexError:
                        uow.balances.insert(
                            Balance(
                                account_id=account_id,
                                month=self._month,
                                amount=delta,
                            )
                        )
        except Exception:
            error.update("Failed to execute transfer")
            return

        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


def _compute_deltas(
    from_account: Account, to_account: Account, amount: int
) -> tuple[int, int]:
    """Compute balance deltas based on account sides.

    The from-account always loses economic value; the to-account always gains it.
    Liabilities are stored as positive amounts, so losing value means an increase.
    """
    from_side = from_account.category.side
    to_side = to_account.category.side

    if from_side == Side.ASSET and to_side == Side.ASSET:
        return (-amount, +amount)
    elif from_side == Side.ASSET and to_side == Side.LIABILITY:
        return (-amount, -amount)
    elif from_side == Side.LIABILITY and to_side == Side.ASSET:
        return (+amount, +amount)
    else:  # LIABILITY -> LIABILITY
        return (+amount, -amount)
