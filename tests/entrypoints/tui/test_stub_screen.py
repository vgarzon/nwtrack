"""Tests for StubScreen placeholder behaviour."""

import asyncio
from unittest.mock import MagicMock

from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.home import HomeScreen


def _make_app() -> NWTrackApp:
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = []
    return NWTrackApp(fetcher=fetcher, uow=MagicMock())


class TestStubScreen:
    def test_stub_screen_shows_section_name_in_subtitle(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                assert app.screen.sub_title == "Reports"

        asyncio.run(_run())

    def test_stub_screen_label_exists(self) -> None:
        async def _run() -> None:
            from textual.widgets import Label

            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                label = app.screen.query_one("#stub-label", Label)
                assert label is not None

        asyncio.run(_run())

    def test_escape_from_stub_pops_to_home(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                stack_depth = len(app.screen_stack)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, HomeScreen)
                assert len(app.screen_stack) == stack_depth - 1

        asyncio.run(_run())
