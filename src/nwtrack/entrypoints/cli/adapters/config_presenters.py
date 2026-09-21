"""Rich-based presenters for configuration use cases."""

from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from nwtrack.application.dto import ConfigFieldInfo, ConfigPathInfo, ConfigValueSource


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

    def confirm_shadow(self, target_path: Path, shadowed_path: Path) -> bool:
        self._console.print(
            f"[warning]{shadowed_path} is currently in effect.[/warning]"
        )
        return self._confirm.ask(
            f"[label]Writing {target_path} will take priority over it going "
            "forward — the existing file will no longer be used. Proceed?"
            "[/label]",
            default=False,
        )

    def show_success(self, path: Path) -> None:
        self._console.print(f"[success]Wrote default config to {path}[/success]")

    def show_cancelled(self) -> None:
        self._console.print(
            "[cancel]Cancelled. Existing config.toml left unchanged.[/cancel]"
        )


def _build_search_paths_table(paths: list[ConfigPathInfo]) -> Table:
    table = Table(title="Config Search Paths")
    table.add_column("Priority", justify="right", style="col.id")
    table.add_column("Path")
    table.add_column("Exists", style="col.status")
    table.add_column("Active", style="col.status")
    for i, info in enumerate(paths, start=1):
        table.add_row(
            str(i),
            str(info.path),
            "yes" if info.exists else "no",
            "[success]yes[/success]" if info.is_active else "",
        )
    return table


_SOURCE_LABELS = {
    ConfigValueSource.ENV: "[warning]env var[/warning]",
    ConfigValueSource.FILE: "config.toml",
    ConfigValueSource.DEFAULT: "[info]default[/info]",
}


def _build_settings_table(fields: list[ConfigFieldInfo]) -> Table:
    table = Table(title="Effective Settings")
    table.add_column("Setting", style="col.name")
    table.add_column("Value")
    table.add_column("Source")
    for f in fields:
        table.add_row(f.name, f.value, _SOURCE_LABELS[f.source])
    return table


class RichShowConfigPresenter:
    """Rich-based implementation of ShowConfigPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def display_search_paths(self, paths: list[ConfigPathInfo]) -> None:
        self._console.print(_build_search_paths_table(paths))

    def display_settings(self, fields: list[ConfigFieldInfo]) -> None:
        self._console.print(_build_settings_table(fields))
