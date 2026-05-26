"""Tests for HomeScreen navigation."""

import asyncio
from unittest.mock import MagicMock

import pytest

from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.balance_update import BalanceUpdateScreen
from nwtrack.entrypoints.tui.screens.home import HomeScreen
from nwtrack.entrypoints.tui.screens.stub import StubScreen


def _make_app() -> NWTrackApp:
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = []
    return NWTrackApp(fetcher=fetcher, uow=MagicMock())


class TestHomeScreenMounts:
    def test_home_screen_is_active_on_launch(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test():
                assert isinstance(app.screen, HomeScreen)

        asyncio.run(_run())


class TestHomeScreenNavigation:
    def test_enter_on_balances_pushes_balance_update_screen(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, BalanceUpdateScreen)

        asyncio.run(_run())

    def test_escape_from_balance_update_returns_to_home(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, HomeScreen)

        asyncio.run(_run())

    @pytest.mark.parametrize(
        "steps,expected_subtitle",
        [
            (1, "Reports"),
            (2, "Accounts"),
            (3, "Admin"),
        ],
    )
    def test_placeholder_items_push_stub_screen(
        self, steps: int, expected_subtitle: str
    ) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                for _ in range(steps):
                    await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, StubScreen)
                assert app.screen.sub_title == expected_subtitle

        asyncio.run(_run())

    def test_escape_from_stub_screen_returns_to_home(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, StubScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, HomeScreen)

        asyncio.run(_run())
