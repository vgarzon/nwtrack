"""Shared utilities for TUI screens."""

from nwtrack.domain.value_objects import Month


def parse_amount_input(raw: str) -> int:
    """Parse a user-entered amount string into cents.

    Accepts integer ("8500") or decimal ("8500.00") strings.
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
    return round(value * 100)


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
