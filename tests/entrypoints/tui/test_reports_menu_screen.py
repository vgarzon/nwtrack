"""Tests for ReportsMenuScreen navigation."""

import asyncio
from unittest.mock import MagicMock

from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.aggregation import AggregationScreen
from nwtrack.entrypoints.tui.screens.networth_history import NetWorthHistoryScreen
from nwtrack.entrypoints.tui.screens.reports_menu import ReportsMenuScreen


def _make_app() -> NWTrackApp:
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = []
    fetcher.get_available_aggregation_months.return_value = []
    return NWTrackApp(fetcher=fetcher, uow=MagicMock())


class TestReportsMenuScreen:
    def test_reports_menu_screen_is_shown_on_reports_selection(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, ReportsMenuScreen)

        asyncio.run(_run())

    def test_subtitle_is_reports(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                assert app.screen.sub_title == "Reports"

        asyncio.run(_run())

    def test_net_worth_history_selection_pushes_screen(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, ReportsMenuScreen)
                await pilot.press("enter")  # Net Worth History (first item)
                await pilot.pause()
                assert isinstance(app.screen, NetWorthHistoryScreen)

        asyncio.run(_run())

    def test_aggregation_selection_pushes_screen(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, ReportsMenuScreen)
                await pilot.press("down")  # Aggregation
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AggregationScreen)

        asyncio.run(_run())

    def test_escape_from_reports_menu_returns_to_home(self) -> None:
        from nwtrack.entrypoints.tui.screens.home import HomeScreen

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
