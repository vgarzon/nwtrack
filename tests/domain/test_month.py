"""
Test Month class methods
"""

from nwtrack.domain.value_objects import Month


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


def test_month_equality() -> None:
    """Test Month equality operator."""
    month1 = Month(2023, 5)
    month2 = Month(2023, 5)
    month3 = Month(2024, 5)
    assert month1 == month2, "Month equality failed for equal months"
    assert month1 != month3, "Month inequality failed for different months"


def test_month_less_than() -> None:
    """Test Month less-than operator."""
    month1 = Month(2023, 5)
    month2 = Month(2023, 6)
    month3 = Month(2024, 1)
    assert month1 < month2, "Month less-than failed for same year"
    assert month2 < month3, "Month less-than failed for different years"


def test_month_sorting() -> None:
    """Test sorting of Month instances."""
    months = [Month(2024, 3), Month(2023, 12), Month(2024, 1), Month(2023, 5)]
    sorted_months = sorted(months)
    expected_order = [Month(2023, 5), Month(2023, 12), Month(2024, 1), Month(2024, 3)]
    assert sorted_months == expected_order, "Month sorting failed"


def test_month_max() -> None:
    """Test max function with Month instances."""
    month1 = Month(2023, 5)
    month2 = Month(2024, 1)
    month3 = Month(2023, 12)
    latest_month = max(month1, month2, month3)
    assert latest_month == month2, "Month max function failed"
