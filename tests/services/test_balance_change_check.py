"""Tests for the balance-change threshold warning helper."""

import pytest

from nwtrack.application.services.balance_change_check import evaluate_balance_change


def test_no_prior_balance_skips_check() -> None:
    result = evaluate_balance_change(
        current_balance=0, new_amount=100_000, threshold_pct=20.0
    )
    assert result is None


@pytest.mark.parametrize("threshold_pct", [0.0, -5.0])
def test_disabled_threshold_skips_check(threshold_pct: float) -> None:
    assert (
        evaluate_balance_change(
            current_balance=10_000, new_amount=1_000_000, threshold_pct=threshold_pct
        )
        is None
    )


def test_change_below_threshold_is_not_flagged() -> None:
    # 10% increase, threshold 20%
    result = evaluate_balance_change(
        current_balance=10_000, new_amount=11_000, threshold_pct=20.0
    )
    assert result is None


def test_change_exactly_at_threshold_is_not_flagged() -> None:
    # Exactly 20% increase, threshold 20% -> strictly-greater-than semantics
    result = evaluate_balance_change(
        current_balance=10_000, new_amount=12_000, threshold_pct=20.0
    )
    assert result is None


def test_large_increase_is_flagged() -> None:
    result = evaluate_balance_change(
        current_balance=100, new_amount=1_000, threshold_pct=20.0
    )
    assert result is not None
    assert result.increased is True
    assert result.pct_change == pytest.approx(900.0)


def test_large_decrease_is_flagged() -> None:
    result = evaluate_balance_change(
        current_balance=1_000, new_amount=100, threshold_pct=20.0
    )
    assert result is not None
    assert result.increased is False
    assert result.pct_change == pytest.approx(90.0)


def test_negative_balances_use_absolute_value_for_pct_change() -> None:
    # Liability-style negative amounts should still compute a sensible pct change.
    result = evaluate_balance_change(
        current_balance=-100, new_amount=-1_000, threshold_pct=20.0
    )
    assert result is not None
    assert result.increased is False
    assert result.pct_change == pytest.approx(900.0)
