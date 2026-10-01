"""Tests for the startup balance check in NWTrackApp."""

import asyncio
from unittest.mock import MagicMock

from nwtrack.application.dto import OperationResult
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.balance_update import BalanceUpdateScreen
from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal
from nwtrack.entrypoints.tui.screens.home import HomeScreen

TODAY = Month(2026, 10)


def _make_app(gap: list[Month], result: OperationResult | None = None):
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = []
    forward_fill = MagicMock()
    forward_fill.find_gap.return_value = gap
    forward_fill.run.return_value = result or OperationResult(success=True, data=8)
    app = NWTrackApp(
        fetcher=fetcher,
        uow=MagicMock(),
        forward_fill=forward_fill,
        current_month=lambda: TODAY,
    )
    return app, forward_fill


def _message(app: NWTrackApp) -> str:
    from textual.widgets import Label

    return str(app.screen.query_one("#confirm-message", Label).render())


class TestStartupBalanceCheck:
    def test_no_prompt_when_no_gap(self) -> None:
        async def _run() -> None:
            app, ff = _make_app([])
            async with app.run_test() as pilot:
                await pilot.pause()
                assert isinstance(app.screen, HomeScreen)
                ff.find_gap.assert_called_once_with(TODAY)
                ff.run.assert_not_called()

        asyncio.run(_run())

    def test_no_check_without_forward_fill(self) -> None:
        async def _run() -> None:
            fetcher = MagicMock()
            fetcher.get_recent_months.return_value = []
            app = NWTrackApp(fetcher=fetcher, uow=MagicMock())
            async with app.run_test() as pilot:
                await pilot.pause()
                assert isinstance(app.screen, HomeScreen)

        asyncio.run(_run())

    def test_prompt_lists_missing_months(self) -> None:
        async def _run() -> None:
            gap = [Month(2026, 8), Month(2026, 9), Month(2026, 10)]
            app, _ = _make_app(gap)
            async with app.run_test() as pilot:
                await pilot.pause()
                assert isinstance(app.screen, ConfirmModal)
                text = _message(app)
                assert "2026-08 → 2026-10" in text
                assert "3 months" in text
                assert "from 2026-07" in text

        asyncio.run(_run())

    def test_prompt_single_month_wording(self) -> None:
        async def _run() -> None:
            app, _ = _make_app([TODAY])
            async with app.run_test() as pilot:
                await pilot.pause()
                text = _message(app)
                assert "2026-10 has no balances." in text
                assert "1 month " in text

        asyncio.run(_run())

    def test_decline_persists_nothing(self) -> None:
        async def _run() -> None:
            app, ff = _make_app([TODAY])
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#btn-cancel")
                await pilot.pause()
                assert isinstance(app.screen, HomeScreen)
                ff.run.assert_not_called()

        asyncio.run(_run())

    def test_approve_fills_and_offers_update(self) -> None:
        async def _run() -> None:
            gap = [Month(2026, 9), Month(2026, 10)]
            app, ff = _make_app(gap)
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#btn-confirm")
                await pilot.pause()
                ff.run.assert_called_once_with(gap)
                assert isinstance(app.screen, ConfirmModal)
                assert "Update balances for 2026-10" in _message(app)

        asyncio.run(_run())

    def test_accepting_update_opens_balance_update_screen(self) -> None:
        async def _run() -> None:
            app, _ = _make_app([TODAY])
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#btn-confirm")
                await pilot.pause()
                await pilot.click("#btn-confirm")
                await pilot.pause()
                assert isinstance(app.screen, BalanceUpdateScreen)

        asyncio.run(_run())

    def test_later_stays_on_home(self) -> None:
        async def _run() -> None:
            app, _ = _make_app([TODAY])
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#btn-confirm")
                await pilot.pause()
                await pilot.click("#btn-cancel")
                await pilot.pause()
                assert isinstance(app.screen, HomeScreen)

        asyncio.run(_run())

    def test_failure_shows_error_and_no_update_prompt(self) -> None:
        async def _run() -> None:
            app, _ = _make_app(
                [TODAY], OperationResult(success=False, error_message="boom")
            )
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#btn-confirm")
                await pilot.pause()
                assert isinstance(app.screen, HomeScreen)

        asyncio.run(_run())
