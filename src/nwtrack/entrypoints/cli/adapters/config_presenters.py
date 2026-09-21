"""Rich-based presenters for configuration use cases."""

from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm


class RichInitConfigPresenter:
    """Rich-based implementation of InitConfigPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console
        self._confirm = Confirm(console=self._console)

    def show_target_path(self, path: Path) -> None:
        self._console.print(f"[bold]Config file target:[/bold] {path}")

    def confirm_overwrite(self, path: Path) -> bool:
        return self._confirm.ask(
            f"[label]{path} already exists. Overwrite?[/label]", default=False
        )

    def show_success(self, path: Path) -> None:
        self._console.print(f"[success]Wrote default config to {path}[/success]")

    def show_cancelled(self) -> None:
        self._console.print(
            "[cancel]Cancelled. Existing config.toml left unchanged.[/cancel]"
        )
