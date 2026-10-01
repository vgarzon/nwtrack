"""
Textual TUI application for nwtrack.
"""

from collections.abc import Callable
from datetime import date

from textual import work
from textual.app import App
from textual.binding import Binding

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.forward_fill_balances import ForwardFillBalances
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal
from nwtrack.entrypoints.tui.screens.home import HomeScreen
from nwtrack.entrypoints.tui.theme import SHARED_CSS


class NWTrackApp(App):
    """nwtrack Textual application."""

    TITLE = "nwtrack"
    CSS = SHARED_CSS
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+t", "toggle_dark", "Toggle theme", priority=True),
    ]

    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
        change_warning_threshold_pct: float = 20.0,
        forward_fill: ForwardFillBalances | None = None,
        current_month: Callable[[], Month] | None = None,
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow
        self._change_warning_threshold_pct = change_warning_threshold_pct
        self._forward_fill = forward_fill
        self._current_month = current_month or _today_month

    def on_mount(self) -> None:
        self.push_screen(
            HomeScreen(
                self._fetcher,
                self._uow,
                change_warning_threshold_pct=self._change_warning_threshold_pct,
            )
        )
        if self._forward_fill is not None:
            self._check_missing_balances(self._forward_fill)

    @work
    async def _check_missing_balances(self, forward_fill: ForwardFillBalances) -> None:
        """Offer to forward-fill months missing between the last balance and today."""
        current = self._current_month()
        gap = forward_fill.find_gap(current)
        if not gap:
            return
        if len(gap) == 1:
            span = f"{gap[0]} has no balances."
        else:
            span = f"{gap[0]} \u2192 {gap[-1]} have no balances."
        source = gap[0].previous()
        approved = await self.push_screen_wait(
            ConfirmModal(
                f"{span}\nRoll forward {len(gap)} "
                f"{'month' if len(gap) == 1 else 'months'} from {source}?",
                confirm_label="Roll forward",
                cancel_label="Not now",
            )
        )
        if not approved:
            return
        result = forward_fill.run(gap)
        if not result.success:
            self.notify(
                result.error_message, title="Roll forward failed", severity="error"
            )
            return
        self.notify(f"Created {result.data} balances through {gap[-1]}.")
        update = await self.push_screen_wait(
            ConfirmModal(
                f"Update balances for {current} now?",
                confirm_label="Update",
                cancel_label="Later",
            )
        )
        if update:
            from nwtrack.entrypoints.tui.screens.balance_update import (
                BalanceUpdateScreen,
            )

            self.push_screen(
                BalanceUpdateScreen(
                    self._fetcher,
                    self._uow,
                    change_warning_threshold_pct=self._change_warning_threshold_pct,
                )
            )


def _today_month() -> Month:
    today = date.today()
    return Month(today.year, today.month)
