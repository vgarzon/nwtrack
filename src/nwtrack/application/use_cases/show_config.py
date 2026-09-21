"""
Show the active config.toml, its search-path priority, and resolved settings.
"""

import logging

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import ShowConfigPresenter
from nwtrack.infra.config.load import describe_settings

logger = logging.getLogger(__name__)


class ShowConfig:
    """Display the config.toml search-path priority and effective settings."""

    def __init__(self, presenter: ShowConfigPresenter) -> None:
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        logger.info("Starting ShowConfig use case")
        result = describe_settings()
        self._presenter.display_search_paths(result.search_paths)
        self._presenter.display_settings(result.fields)
        logger.info("Finished ShowConfig")
        return OperationResult(success=True)


def main() -> int:
    from rich.console import Console

    from nwtrack.bootstrap.container import Container, Lifetime
    from nwtrack.entrypoints.cli.adapters.config_presenters import (
        RichShowConfigPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    container = Container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        RichShowConfigPresenter,
        lambda c: RichShowConfigPresenter(console=c.resolve(Console)),
    ).register(
        ShowConfig,
        lambda c: ShowConfig(presenter=c.resolve(RichShowConfigPresenter)),
    )

    op: OperationResult[None] = container.resolve(ShowConfig).run()
    return 0 if op.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
