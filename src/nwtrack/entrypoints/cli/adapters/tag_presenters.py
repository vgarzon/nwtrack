"""Rich-based presenters for tag-related use cases."""

from rich.console import Console

from nwtrack.application.dto import TagListItem
from nwtrack.entrypoints.cli.ui.renderers import build_tags_table


class RichTagListPresenter:
    """Rich-based implementation of TagListPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def display_tags(self, tags: list[TagListItem]) -> None:
        """Display tags table using Rich."""
        if not tags:
            self._console.print("[info]No tags found.[/info]")
            return
        self._console.print(build_tags_table(tags))
