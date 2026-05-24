"""Unit tests for TUI utility helpers."""

import pytest

from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.utils import months_to_grid, parse_amount_input


class TestParseAmountInput:
    def test_integer_string(self) -> None:
        assert parse_amount_input("8500") == 850000

    def test_decimal_string(self) -> None:
        assert parse_amount_input("8500.00") == 850000

    def test_decimal_with_cents(self) -> None:
        assert parse_amount_input("8500.50") == 850050

    def test_whitespace_stripped(self) -> None:
        assert parse_amount_input("  1000  ") == 100000

    def test_zero_is_valid(self) -> None:
        assert parse_amount_input("0") == 0

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_amount_input("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_amount_input("   ")

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_amount_input("abc")

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_amount_input("-500")


class TestMonthsToGrid:
    def test_empty_list(self) -> None:
        assert months_to_grid([]) == []

    def test_fewer_than_one_row(self) -> None:
        months = [Month(2026, 1), Month(2026, 2)]
        result = months_to_grid(months, cols=3)
        assert result == [[Month(2026, 1), Month(2026, 2)]]

    def test_exact_multiple_of_cols(self) -> None:
        months = [Month(2026, m) for m in range(1, 7)]
        result = months_to_grid(months, cols=3)
        assert len(result) == 2
        assert result[0] == [Month(2026, 1), Month(2026, 2), Month(2026, 3)]
        assert result[1] == [Month(2026, 4), Month(2026, 5), Month(2026, 6)]

    def test_non_multiple_of_cols(self) -> None:
        months = [Month(2026, m) for m in range(1, 5)]
        result = months_to_grid(months, cols=3)
        assert len(result) == 2
        assert len(result[0]) == 3
        assert len(result[1]) == 1

    def test_single_month(self) -> None:
        months = [Month(2026, 3)]
        result = months_to_grid(months, cols=3)
        assert result == [[Month(2026, 3)]]
