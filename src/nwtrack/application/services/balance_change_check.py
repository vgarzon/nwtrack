"""
Shared logic for warning on large balance changes.
"""

from nwtrack.application.dto import BalanceChangeWarning


def evaluate_balance_change(
    current_balance: int, new_amount: int, threshold_pct: float
) -> BalanceChangeWarning | None:
    """Determine whether a balance change should trigger a confirmation warning.

    Args:
        current_balance: The account's prior balance for the month, or 0 if none exists.
        new_amount: The newly entered balance amount.
        threshold_pct: Percent-change threshold above which to warn. A value <= 0
            disables the check.

    Returns:
        A BalanceChangeWarning if the percent change from current_balance to
        new_amount strictly exceeds threshold_pct, otherwise None. Always None
        when there is no prior balance (current_balance == 0) or the threshold
        is disabled (threshold_pct <= 0).
    """
    if current_balance == 0 or threshold_pct <= 0:
        return None

    pct_change = abs(new_amount - current_balance) / abs(current_balance) * 100
    if pct_change <= threshold_pct:
        return None

    return BalanceChangeWarning(
        pct_change=pct_change, increased=new_amount > current_balance
    )
