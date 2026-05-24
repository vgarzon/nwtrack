"""
TUI launch command.
"""

import typer

from nwtrack.entrypoints.cli.app import tui_app


@tui_app.command("launch")
def launch() -> None:
    """Launch the Textual TUI application."""
    import nwtrack.entrypoints.tui.app as tui

    tui.NWTrackApp().run()
