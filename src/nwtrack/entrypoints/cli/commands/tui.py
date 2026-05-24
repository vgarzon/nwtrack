"""
TUI launch command.
"""

from collections.abc import Callable

from nwtrack.entrypoints.cli.app import tui_app


@tui_app.command("launch")
def launch() -> None:
    """Launch the Textual TUI application."""
    from dotenv import load_dotenv

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.fetch import FetchService
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.bootstrap.tui_composition import build_tui_container
    from nwtrack.entrypoints.tui.app import NWTrackApp

    load_dotenv()
    setup_logging()

    container = build_tui_container()
    fetcher: FetchService = container.resolve(FetchService)
    uow: Callable[[], UnitOfWork] = lambda: container.resolve(UnitOfWork)  # noqa: E731

    NWTrackApp(fetcher=fetcher, uow=uow).run()
