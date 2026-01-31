"""
Rich console for enhanced terminal output.
"""

from dataclasses import dataclass

from rich.console import Console
from rich.theme import Theme


@dataclass(frozen=True)
class ConsoleSettings:
    """Settings for the Rich console."""

    theme: Theme = Theme(
        {
            "success": "green",
            "info": "dim cyan",
            "warning": "magenta",
            "error": "bold red",
        }
    )
    width: int | None = None
    record: bool = False


def build_console(settings: ConsoleSettings | None = None) -> Console:
    """Build and return a Rich console with the given settings.

    Args:
        settings (ConsoleSettings | None): Settings for the console.
            If None, default settings are used.

    Returns:
        Console: Configured Rich console instance.
    """
    settings = settings or ConsoleSettings()

    console = Console(
        theme=settings.theme,
        width=settings.width,
        record=settings.record,
    )
    return console
