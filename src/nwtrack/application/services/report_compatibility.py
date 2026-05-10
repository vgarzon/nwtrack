"""Helpers for adapting shared aggregation results to legacy report DTOs."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from nwtrack.application.dto import (
    AggregationDimension,
    HistoryAggregationResult,
    MonthlyCategoryBalance,
    SingleMonthAggregationResult,
)
from nwtrack.domain.models import Category, NetWorth, Side


def to_monthly_category_balances(
    result: SingleMonthAggregationResult,
    category_sides: Mapping[str, Side],
) -> list[MonthlyCategoryBalance]:
    """Adapt shared category aggregation rows to the legacy category DTO shape."""
    if result.dimension != AggregationDimension.CATEGORY:
        raise ValueError("Category compatibility mapping requires category aggregation.")

    monthly_balances: list[MonthlyCategoryBalance] = []
    for group in result.groups:
        monthly_balances.append(
            MonthlyCategoryBalance(
                month=result.month,
                category=Category(
                    name=group.label,
                    side=category_sides[group.label],
                ),
                amount=group.amount,
            )
        )
    return monthly_balances


def to_networth(
    result: SingleMonthAggregationResult,
) -> NetWorth | None:
    """Adapt shared single-month side aggregation to the legacy net-worth DTO."""
    if result.dimension != AggregationDimension.SIDE:
        raise ValueError("Net worth compatibility mapping requires side aggregation.")
    if not result.groups:
        return None

    assets, liabilities = _sum_side_groups((group.label, group.amount) for group in result.groups)
    currency_code = result.currency_code or result.groups[0].currency_code

    return NetWorth(
        month=result.month,
        currency_code=currency_code,
        assets=assets,
        liabilities=liabilities,
        net_worth=assets - liabilities,
    )


def to_networth_history(
    result: HistoryAggregationResult,
) -> list[NetWorth]:
    """Adapt shared side-history rows to the legacy net-worth history DTO shape."""
    if result.dimension != AggregationDimension.SIDE:
        raise ValueError("Net worth compatibility mapping requires side aggregation.")

    rows_by_month: dict = defaultdict(list)
    for row in result.rows:
        rows_by_month[row.month].append((row.label, row.amount, row.currency_code))

    networth_history: list[NetWorth] = []
    for month in sorted(rows_by_month):
        month_rows = rows_by_month[month]
        assets, liabilities = _sum_side_groups((label, amount) for label, amount, _ in month_rows)
        currency_code = result.currency_code or month_rows[0][2]
        networth_history.append(
            NetWorth(
                month=month,
                currency_code=currency_code,
                assets=assets,
                liabilities=liabilities,
                net_worth=assets - liabilities,
            )
        )
    return networth_history


def _sum_side_groups(groups) -> tuple[int, int]:
    assets = 0
    liabilities = 0
    for label, amount in groups:
        if label == Side.ASSET.value:
            assets += amount
        elif label == Side.LIABILITY.value:
            liabilities += amount
        else:
            raise ValueError(f"Unsupported side label for net worth mapping: {label}")
    return assets, liabilities
