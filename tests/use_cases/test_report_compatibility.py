"""Tests for shared-to-legacy reporting compatibility mappers."""

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    HistoryAggregationResult,
    HistoryAggregationRow,
    SingleMonthAggregationGroup,
    SingleMonthAggregationResult,
)
from nwtrack.application.services.report_compatibility import (
    to_monthly_category_balances,
    to_networth,
    to_networth_history,
)
from nwtrack.domain.models import Side
from nwtrack.domain.value_objects import Month


def test_to_monthly_category_balances_adapts_shared_groups() -> None:
    """Category compatibility mapping should preserve month, label, and amount."""
    result = SingleMonthAggregationResult(
        month=Month(2025, 11),
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        status_scope=AccountStatusScope.ACTIVE,
        groups=[
            SingleMonthAggregationGroup(
                group_key="checking",
                label="checking",
                amount=200,
                currency_code="USD",
            ),
            SingleMonthAggregationGroup(
                group_key="revolving_credit",
                label="revolving_credit",
                amount=600,
                currency_code="USD",
            ),
        ],
    )

    balances = to_monthly_category_balances(
        result,
        {
            "checking": Side.ASSET,
            "revolving_credit": Side.LIABILITY,
        },
    )

    assert [(row.category.name, row.category.side, row.amount) for row in balances] == [
        ("checking", Side.ASSET, 200),
        ("revolving_credit", Side.LIABILITY, 600),
    ]


def test_to_networth_maps_single_month_side_groups() -> None:
    """Single-month side aggregation should adapt into a legacy net-worth row."""
    result = SingleMonthAggregationResult(
        month=Month(2025, 11),
        dimension=AggregationDimension.SIDE,
        currency_code="USD",
        status_scope=AccountStatusScope.ACTIVE,
        groups=[
            SingleMonthAggregationGroup(
                group_key="asset",
                label="asset",
                amount=700,
                currency_code="USD",
            ),
            SingleMonthAggregationGroup(
                group_key="liability",
                label="liability",
                amount=600,
                currency_code="USD",
            ),
        ],
    )

    networth = to_networth(result)

    assert networth is not None
    assert (networth.assets, networth.liabilities, networth.net_worth) == (
        700,
        600,
        100,
    )


def test_to_networth_history_groups_history_rows_by_month() -> None:
    """History side aggregation should adapt into chronological net-worth rows."""
    result = HistoryAggregationResult(
        start_month=Month(2025, 10),
        end_month=Month(2025, 11),
        dimension=AggregationDimension.SIDE,
        currency_code="USD",
        status_scope=AccountStatusScope.ACTIVE,
        rows=[
            HistoryAggregationRow(
                month=Month(2025, 11),
                group_key="asset",
                label="asset",
                amount=700,
                currency_code="USD",
            ),
            HistoryAggregationRow(
                month=Month(2025, 10),
                group_key="liability",
                label="liability",
                amount=700,
                currency_code="USD",
            ),
            HistoryAggregationRow(
                month=Month(2025, 10),
                group_key="asset",
                label="asset",
                amount=900,
                currency_code="USD",
            ),
            HistoryAggregationRow(
                month=Month(2025, 11),
                group_key="liability",
                label="liability",
                amount=600,
                currency_code="USD",
            ),
        ],
    )

    networth_history = to_networth_history(result)

    assert [
        (row.month, row.assets, row.liabilities, row.net_worth)
        for row in networth_history
    ] == [
        (Month(2025, 10), 900, 700, 200),
        (Month(2025, 11), 700, 600, 100),
    ]
