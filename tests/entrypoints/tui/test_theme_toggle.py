"""Tests for the global dark/light theme toggle."""

import asyncio
from unittest.mock import MagicMock

from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.home import HomeScreen


def _make_app() -> NWTrackApp:
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = []
    return NWTrackApp(fetcher=fetcher, uow=MagicMock())


class TestThemeToggle:
    def test_toggle_binding_flips_theme(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                start_theme = app.theme
                await pilot.press("d")
                await pilot.pause()
                assert app.theme != start_theme

        asyncio.run(_run())

    def test_toggle_twice_returns_to_original_theme(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                start_theme = app.theme
                await pilot.press("d")
                await pilot.pause()
                await pilot.press("d")
                await pilot.pause()
                assert app.theme == start_theme

        asyncio.run(_run())

    def test_home_screen_indicator_reflects_mode(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                assert isinstance(app.screen, HomeScreen)
                initial_dark = app.current_theme.dark
                assert app.screen.sub_title == (
                    "Dark mode" if initial_dark else "Light mode"
                )

                await pilot.press("d")
                await pilot.pause()

                toggled_dark = app.current_theme.dark
                assert toggled_dark != initial_dark
                assert app.screen.sub_title == (
                    "Dark mode" if toggled_dark else "Light mode"
                )

        asyncio.run(_run())
