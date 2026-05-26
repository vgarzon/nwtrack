"""Tests for HomeScreen navigation."""

import asyncio
from unittest.mock import MagicMock

from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.accounts import AccountsListScreen
from nwtrack.entrypoints.tui.screens.admin_menu import AdminMenuScreen
from nwtrack.entrypoints.tui.screens.balance_update import BalanceUpdateScreen
from nwtrack.entrypoints.tui.screens.home import HomeScreen
from nwtrack.entrypoints.tui.screens.reports_menu import ReportsMenuScreen


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

    def test_reports_pushes_reports_menu_screen(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, ReportsMenuScreen)
                assert app.screen.sub_title == "Reports"

        asyncio.run(_run())

    def test_escape_from_reports_menu_returns_to_home(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, ReportsMenuScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, HomeScreen)

        asyncio.run(_run())

    def test_accounts_pushes_accounts_list_screen(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("down")
                await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AccountsListScreen)

        asyncio.run(_run())

    def test_admin_pushes_admin_menu_screen(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                for _ in range(3):
                    await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AdminMenuScreen)

        asyncio.run(_run())
