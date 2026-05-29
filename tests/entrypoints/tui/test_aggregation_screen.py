"""Tests for AggregationScreen."""

import asyncio
from unittest.mock import MagicMock

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    SingleMonthAggregationGroup,
    SingleMonthAggregationResult,
)
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.aggregation import AggregationScreen


def _make_months(*ym: tuple[int, int]) -> list[Month]:
    return [Month(y, m) for y, m in ym]


def _make_agg_result(
    month: Month,
    dimension: AggregationDimension,
    groups: list[SingleMonthAggregationGroup],
) -> SingleMonthAggregationResult:
    return SingleMonthAggregationResult(
        month=month,
        dimension=dimension,
        currency_code=None,
        status_scope=AccountStatusScope.ACTIVE,
        groups=groups,
    )


def _make_app(
    available_months: list[Month],
    agg_result: SingleMonthAggregationResult | None = None,
) -> NWTrackApp:
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = []
    fetcher.get_available_aggregation_months.return_value = available_months

    uow_factory = MagicMock()
    mock_uow = MagicMock()
    uow_factory.return_value.__enter__ = MagicMock(return_value=mock_uow)
    uow_factory.return_value.__exit__ = MagicMock(return_value=False)
    mock_uow.reporting.get_month_currencies.return_value = ["USD"]
    if agg_result is not None:
        mock_uow.reporting.aggregate_single_month.return_value = agg_result

    return NWTrackApp(fetcher=fetcher, uow=uow_factory)


class TestAggregationScreenNavigation:
    def test_screen_pushes_from_reports_menu(self) -> None:
        months = _make_months((2025, 3),)
        groups = [SingleMonthAggregationGroup("cat1", "Savings", 50_000, "USD")]
        result = _make_agg_result(months[0], AggregationDimension.CATEGORY, groups)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")  # Aggregation
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AggregationScreen)

        asyncio.run(_run())

    def test_escape_from_screen_pops_to_reports_menu(self) -> None:
        from nwtrack.entrypoints.tui.screens.reports_menu import ReportsMenuScreen

        months = _make_months((2025, 3),)
        groups = [SingleMonthAggregationGroup("cat1", "Savings", 50_000, "USD")]
        result = _make_agg_result(months[0], AggregationDimension.CATEGORY, groups)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")  # Aggregation
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AggregationScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, ReportsMenuScreen)

        asyncio.run(_run())

    def test_no_available_months_shows_error(self) -> None:
        from textual.widgets import Label

        app = _make_app(available_months=[])

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")  # Aggregation
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AggregationScreen)
                label = app.screen.query_one("#error-label", Label)
                assert label.display is True

        asyncio.run(_run())

    def test_default_month_is_most_recent(self) -> None:
        months = _make_months((2025, 1), (2025, 2), (2025, 3))
        groups = [SingleMonthAggregationGroup("cat1", "Savings", 50_000, "USD")]
        result = _make_agg_result(months[-1], AggregationDimension.CATEGORY, groups)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")  # Aggregation
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AggregationScreen)
                assert app.screen._month == months[-1]

        asyncio.run(_run())

    def test_default_status_scope_is_historical(self) -> None:
        months = _make_months((2025, 3),)
        groups = [SingleMonthAggregationGroup("cat1", "Savings", 50_000, "USD")]
        result = _make_agg_result(months[0], AggregationDimension.CATEGORY, groups)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")  # Aggregation
                await pilot.press("enter")
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, AggregationScreen)
                assert screen._status_scope == AccountStatusScope.HISTORICAL

        asyncio.run(_run())

    def test_scope_selector_widget_is_present(self) -> None:
        from textual.widgets import RadioSet

        months = _make_months((2025, 3),)
        groups = [SingleMonthAggregationGroup("cat1", "Savings", 50_000, "USD")]
        result = _make_agg_result(months[0], AggregationDimension.CATEGORY, groups)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")  # Aggregation
                await pilot.press("enter")
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, AggregationScreen)
                selector = screen.query_one("#scope-selector", RadioSet)
                assert selector is not None

        asyncio.run(_run())

    def test_scope_change_to_active_updates_status_scope(self) -> None:
        from textual.widgets import RadioButton, RadioSet

        months = _make_months((2025, 3),)
        groups = [SingleMonthAggregationGroup("cat1", "Savings", 50_000, "USD")]
        result = _make_agg_result(months[0], AggregationDimension.CATEGORY, groups)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")  # Aggregation
                await pilot.press("enter")
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, AggregationScreen)
                radio_set = screen.query_one("#scope-selector", RadioSet)
                active_btn = screen.query_one("#scope-active", RadioButton)
                radio_set.post_message(RadioSet.Changed(radio_set, active_btn))
                await pilot.pause()
                assert screen._status_scope == AccountStatusScope.ACTIVE

        asyncio.run(_run())

    def test_scope_change_to_all_updates_status_scope(self) -> None:
        from textual.widgets import RadioButton, RadioSet

        months = _make_months((2025, 3),)
        groups = [SingleMonthAggregationGroup("cat1", "Savings", 50_000, "USD")]
        result = _make_agg_result(months[0], AggregationDimension.CATEGORY, groups)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")  # Aggregation
                await pilot.press("enter")
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, AggregationScreen)
                radio_set = screen.query_one("#scope-selector", RadioSet)
                all_btn = screen.query_one("#scope-all", RadioButton)
                radio_set.post_message(RadioSet.Changed(radio_set, all_btn))
                await pilot.pause()
                assert screen._status_scope == AccountStatusScope.ALL

        asyncio.run(_run())

    def test_default_dimension_is_category(self) -> None:
        months = _make_months((2025, 3),)
        groups = [SingleMonthAggregationGroup("cat1", "Savings", 50_000, "USD")]
        result = _make_agg_result(months[0], AggregationDimension.CATEGORY, groups)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")  # Aggregation
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AggregationScreen)
                assert app.screen._dimension == AggregationDimension.CATEGORY

        asyncio.run(_run())


class TestAggregationScreenHelpers:
    def test_show_error_makes_label_visible_and_clears_table(self) -> None:
        from textual.widgets import DataTable, Label

        months = _make_months((2025, 3),)
        groups = [SingleMonthAggregationGroup("cat1", "Savings", 50_000, "USD")]
        result = _make_agg_result(months[0], AggregationDimension.CATEGORY, groups)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")  # Aggregation
                await pilot.press("enter")
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, AggregationScreen)
                screen._show_error("Mixed currencies")
                label = screen.query_one("#error-label", Label)
                assert label.display is True
                table = screen.query_one("#agg-table", DataTable)
                assert table.row_count == 0

        asyncio.run(_run())
