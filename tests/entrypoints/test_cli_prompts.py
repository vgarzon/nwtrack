"""Tests for shared CLI prompt parsing helpers."""

from nwtrack.entrypoints.cli.ui.prompts import parse_optional_tag_choices


def test_parse_optional_tag_choices_accepts_none_path() -> None:
    """The explicit no-tags path should return an empty selection."""
    assert parse_optional_tag_choices("0", 3) == []


def test_parse_optional_tag_choices_deduplicates_and_sorts() -> None:
    """Selected indices should normalize to deterministic table order."""
    assert parse_optional_tag_choices("3, 1, 3,2", 3) == [1, 2, 3]


def test_parse_optional_tag_choices_rejects_invalid_values() -> None:
    """Malformed or out-of-range values should fail validation."""
    assert parse_optional_tag_choices("", 3) is None
    assert parse_optional_tag_choices("1,,2", 3) is None
    assert parse_optional_tag_choices("4", 3) is None
    assert parse_optional_tag_choices("abc", 3) is None
