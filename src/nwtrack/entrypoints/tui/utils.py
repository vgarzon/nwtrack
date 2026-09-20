"""Shared utilities for TUI screens."""

from rich.console import JustifyMethod
from rich.text import Text
from textual.app import App

from nwtrack.domain.value_objects import Month


def parse_amount_input(raw: str) -> int:
    """Parse a user-entered amount string into a whole-number balance.

    Accepts integer strings ("8500"). Decimal input is truncated to the
    nearest whole number to match the integer storage model.
    Raises ValueError for empty, non-numeric, or negative input.
    """
    stripped = raw.strip()
    if not stripped:
        raise ValueError("Amount cannot be empty")
    try:
        value = float(stripped)
    except ValueError:
        raise ValueError(f"Invalid amount: {stripped!r}")
    if value < 0:
        raise ValueError("Amount cannot be negative")
    return int(value)


def months_to_grid(months: list[Month], cols: int = 3) -> list[list[Month]]:
    """Arrange a flat list of months into a row-major grid.

    Args:
        months: Months to arrange (any order).
        cols: Number of columns in the grid.

    Returns:
        List of rows, each row a list of up to `cols` months.
    """
    if not months:
        return []
    return [months[i : i + cols] for i in range(0, len(months), cols)]


_FALLBACK_SUCCESS = "green"
_FALLBACK_ERROR = "red"


def delta_text(
    value: int, app: App, *, justify: JustifyMethod | None = "right"
) -> Text:
    """Format a signed delta as Text, colored by direction.

    Positive deltas use the active theme's success color, negative deltas
    use its error color, and zero stays the default (neutral) text color —
    "+0" isn't a gain or a loss. Pulling the color from `app.current_theme`
    (rather than a hardcoded "green"/"red") keeps it correct across themes;
    the plain color names are only a fallback for the (untyped-as-required)
    case where a theme doesn't define one.
    `justify` defaults to "right" for DataTable cells; pass `None` when
    assembling the value inline into a sentence (e.g. a summary Label).
    """
    sign = "+" if value >= 0 else ""
    text = Text(f"{sign}{value:,}", justify=justify)
    if value > 0:
        text.stylize(app.current_theme.success or _FALLBACK_SUCCESS)
    elif value < 0:
        text.stylize(app.current_theme.error or _FALLBACK_ERROR)
    return text
