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
            # Status messages
            "success": "green",
            "info": "dim cyan",
            "warning": "yellow",
            "error": "bold red",
            "cancel": "yellow",
            "label": "yellow",
            "validation": "magenta",
            # Section headers (used in Rule() titles)
            "header": "bold green",
            "header.danger": "bold red",
            "header.info": "bold cyan",
            # Table column styles
            "col.id": "cyan",
            "col.name": "magenta",
            "col.category": "green",
            "col.side": "yellow",
            "col.amount": "bright_white",
            "col.asset": "green",
            "col.liability": "yellow",
            "col.networth": "bold cyan",
            "col.total": "bold",
            "col.month": "cyan",
            "col.count": "magenta",
            "col.code": "magenta",
            "col.desc": "green",
            "col.status": "magenta",
            # Inline delta indicators (transfer preview)
            "delta.positive": "green",
            "delta.negative": "red",
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
