"""
Test Month class methods
"""

from nwtrack.models import Month


def test_month_str_repr() -> None:
    """Test Month __str__ and __repr__ methods."""
    month = Month(2023, 5)
    assert str(month) == "2023-05", "Month __str__ method failed"
    assert repr(month) == "2023-05", "Month __repr__ method failed"


def test_month_parse() -> None:
    """Test Month.parse method."""
    month_str = "2024-12"
    month = Month.parse(month_str)
    assert isinstance(month, Month), "Month.parse did not return Month instance"
    assert month.year == 2024, "Month.parse year mismatch"
    assert month.month == 12, "Month.parse month mismatch"


def test_month_increment() -> None:
    """Test Month.increment method."""
    month = Month(2023, 12)
    next_month = month.increment()
    assert isinstance(next_month, Month), (
        "Month.increment did not return Month instance"
    )
    assert next_month.year == 2024, "Month.increment year mismatch"
    assert next_month.month == 1, "Month.increment month mismatch"

    month = Month(2023, 5)
    next_month = month.increment()
    assert next_month.year == 2023, "Month.increment year mismatch for non-December"
    assert next_month.month == 6, "Month.increment month mismatch for non-December"
