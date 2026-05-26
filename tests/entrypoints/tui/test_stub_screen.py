"""Tests for StubScreen placeholder behaviour.

The StubScreen is kept as a fallback but is no longer used by default navigation
paths — Accounts and Admin now route to real screens. These tests verify the
StubScreen itself still works correctly when used directly.
"""

import asyncio

from textual.app import App, ComposeResult

from nwtrack.entrypoints.tui.screens.stub import StubScreen


class _StubApp(App):
    """Minimal app that pushes a StubScreen immediately."""

    def compose(self) -> ComposeResult:
        from textual.widgets import Label

        yield Label("root")

    def on_mount(self) -> None:
        self.push_screen(StubScreen("TestSection"))


class TestStubScreen:
    def test_stub_screen_shows_section_name_in_subtitle(self) -> None:
        async def _run() -> None:
            app = _StubApp()
            async with app.run_test() as pilot:
                await pilot.pause()
                assert app.screen.sub_title == "TestSection"

        asyncio.run(_run())

    def test_stub_screen_label_exists(self) -> None:
        async def _run() -> None:
            from textual.widgets import Label

            app = _StubApp()
            async with app.run_test() as pilot:
                await pilot.pause()
                label = app.screen.query_one("#stub-label", Label)
                assert label is not None

        asyncio.run(_run())

    def test_escape_from_stub_pops_screen(self) -> None:
        async def _run() -> None:
            app = _StubApp()
            async with app.run_test() as pilot:
                await pilot.pause()
                assert isinstance(app.screen, StubScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert not isinstance(app.screen, StubScreen)

        asyncio.run(_run())
