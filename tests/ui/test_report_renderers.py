"""Renderer tests for grouped report output."""

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    HistoryAggregationResult,
    HistoryAggregationRow,
    SingleMonthAggregationGroup,
    SingleMonthAggregationResult,
)
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.renderers import (
    build_history_aggregation_table,
    build_single_month_aggregation_table,
)


def test_grouped_table_uses_selected_dimension_as_first_column() -> None:
    """The grouped table should label its first column with the selected dimension."""
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
            )
        ],
    )

    table = build_single_month_aggregation_table(result)

    assert [column.header for column in table.columns] == ["Category", "Amount"]


def test_currency_grouped_table_keeps_one_currency_column() -> None:
    """Currency aggregation should render one currency label column."""
    result = SingleMonthAggregationResult(
        month=Month(2025, 11),
        dimension=AggregationDimension.CURRENCY,
        currency_code=None,
        status_scope=AccountStatusScope.ACTIVE,
        groups=[
            SingleMonthAggregationGroup(
                group_key="USD",
                label="USD",
                amount=1300,
                currency_code="USD",
            )
        ],
    )

    table = build_single_month_aggregation_table(result)

    assert [column.header for column in table.columns] == ["Currency", "Amount"]


def test_history_grouped_table_uses_month_and_selected_dimension_columns() -> None:
    """The history table should label its columns for month, dimension, and amount."""
    result = HistoryAggregationResult(
        start_month=Month(2025, 9),
        end_month=Month(2025, 11),
        dimension=AggregationDimension.CATEGORY,
        currency_code="USD",
        status_scope=AccountStatusScope.ACTIVE,
        rows=[
            HistoryAggregationRow(
                month=Month(2025, 9),
                group_key="checking",
                label="checking",
                amount=200,
                currency_code="USD",
            )
        ],
    )

    table = build_history_aggregation_table(result)

    assert [column.header for column in table.columns] == ["Month", "Category", "Amount"]


def test_currency_history_grouped_table_keeps_one_currency_label_column() -> None:
    """Currency history aggregation should render month and currency columns."""
    result = HistoryAggregationResult(
        start_month=Month(2025, 9),
        end_month=Month(2025, 11),
        dimension=AggregationDimension.CURRENCY,
        currency_code=None,
        status_scope=AccountStatusScope.ACTIVE,
        rows=[
            HistoryAggregationRow(
                month=Month(2025, 9),
                group_key="USD",
                label="USD",
                amount=1300,
                currency_code="USD",
            )
        ],
    )

    table = build_history_aggregation_table(result)

    assert [column.header for column in table.columns] == ["Month", "Currency", "Amount"]
