"""Tests for the global dark/light theme toggle."""

import asyncio
from unittest.mock import MagicMock

from textual.widgets import Input

from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.home import HomeScreen
from nwtrack.entrypoints.tui.screens.institutions import InstitutionFormModal


def _make_app() -> NWTrackApp:
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = []
    fetcher.get_all_institutions.return_value = []
    return NWTrackApp(fetcher=fetcher, uow=MagicMock())


class TestThemeToggle:
    def test_toggle_binding_flips_theme(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                start_theme = app.theme
                await pilot.press("ctrl+t")
                await pilot.pause()
                assert app.theme != start_theme

        asyncio.run(_run())

    def test_toggle_twice_returns_to_original_theme(self) -> None:
        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                start_theme = app.theme
                await pilot.press("ctrl+t")
                await pilot.pause()
                await pilot.press("ctrl+t")
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

                await pilot.press("ctrl+t")
                await pilot.pause()

                toggled_dark = app.current_theme.dark
                assert toggled_dark != initial_dark
                assert app.screen.sub_title == (
                    "Dark mode" if toggled_dark else "Light mode"
                )

        asyncio.run(_run())

    def test_toggle_works_while_input_is_focused_in_a_modal(self) -> None:
        """A non-priority binding on a letter key would be swallowed by a
        focused Input instead of reaching the app — regression coverage for
        that failure mode, since every form modal auto-focuses an Input.
        """

        async def _run() -> None:
            app = _make_app()
            async with app.run_test() as pilot:
                for _ in range(3):
                    await pilot.press("down")  # Admin
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")  # Institutions (first admin item)
                await pilot.pause()
                await pilot.press("c")  # open create modal
                await pilot.pause()
                assert isinstance(app.screen, InstitutionFormModal)

                name_input = app.screen.query_one("#input-name", Input)
                assert app.focused is name_input
                start_theme = app.theme

                await pilot.press("ctrl+t")
                await pilot.pause()

                assert app.theme != start_theme
                assert name_input.value == ""

        asyncio.run(_run())


class TestLightModeScreenSmoke:
    """Confirm representative full screens and modals mount cleanly once the
    app is already in light mode — a plain dark-mode pytest run can't catch
    a CSS rule that only misbehaves under the light theme's variable set.
    """

    def test_full_screen_and_modals_mount_in_light_mode(self) -> None:
        async def _run() -> None:
            from nwtrack.entrypoints.tui.screens.categories import (
                CategoryFormModal,
            )
            from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal

            app = _make_app()
            async with app.run_test() as pilot:
                app.theme = "textual-light"
                await pilot.pause()
                assert app.current_theme.dark is False

                for _ in range(3):
                    await pilot.press("down")  # Admin
                await pilot.press("enter")
                await pilot.pause()
                for _ in range(2):
                    await pilot.press("down")  # Categories (3rd admin item)
                await pilot.press("enter")
                await pilot.pause()

                await pilot.press("c")  # CategoryFormModal — .modal-container
                await pilot.pause()
                assert isinstance(app.screen, CategoryFormModal)
                await pilot.press("escape")
                await pilot.pause()

                await app.push_screen(
                    ConfirmModal("Delete this?")
                )  # .modal-container-warning
                await pilot.pause()
                assert isinstance(app.screen, ConfirmModal)

        asyncio.run(_run())
