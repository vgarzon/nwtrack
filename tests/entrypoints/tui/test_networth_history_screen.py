"""Tests for NetWorthHistoryScreen."""

import asyncio
from unittest.mock import MagicMock

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    HistoryAggregationResult,
    HistoryAggregationRow,
)
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.networth_history import NetWorthHistoryScreen


def _make_months(*ym: tuple[int, int]) -> list[Month]:
    return [Month(y, m) for y, m in ym]


def _make_history_result(
    months: list[Month],
    rows: list[HistoryAggregationRow],
) -> HistoryAggregationResult:
    return HistoryAggregationResult(
        start_month=months[0],
        end_month=months[-1],
        dimension=AggregationDimension.SIDE,
        currency_code="USD",
        status_scope=AccountStatusScope.ALL,
        rows=rows,
    )


def _make_app(
    available_months: list[Month],
    agg_result: HistoryAggregationResult | None = None,
) -> NWTrackApp:
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = []
    fetcher.get_available_aggregation_months.return_value = available_months

    uow_factory = MagicMock()
    mock_uow = MagicMock()
    uow_factory.return_value.__enter__ = MagicMock(return_value=mock_uow)
    uow_factory.return_value.__exit__ = MagicMock(return_value=False)
    if agg_result is not None:
        mock_uow.reporting.aggregate_history.return_value = agg_result

    return NWTrackApp(fetcher=fetcher, uow=uow_factory)


class TestNetWorthHistoryScreenNavigation:
    def test_screen_pushes_from_reports_menu(self) -> None:
        months = _make_months((2025, 1), (2025, 2))
        rows = [
            HistoryAggregationRow(Month(2025, 1), "asset", "asset", 100_000, "USD"),
            HistoryAggregationRow(Month(2025, 1), "liability", "liability", 40_000, "USD"),  # noqa: E501
        ]
        result = _make_history_result(months, rows)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")  # Net Worth History
                await pilot.pause()
                assert isinstance(app.screen, NetWorthHistoryScreen)

        asyncio.run(_run())

    def test_escape_from_screen_pops_to_reports_menu(self) -> None:
        from nwtrack.entrypoints.tui.screens.reports_menu import ReportsMenuScreen

        months = _make_months((2025, 1), (2025, 2))
        rows = [
            HistoryAggregationRow(Month(2025, 1), "asset", "asset", 100_000, "USD"),
            HistoryAggregationRow(Month(2025, 1), "liability", "liability", 40_000, "USD"),  # noqa: E501
        ]
        result = _make_history_result(months, rows)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")  # Net Worth History
                await pilot.pause()
                assert isinstance(app.screen, NetWorthHistoryScreen)
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
                await pilot.press("enter")  # Net Worth History
                await pilot.pause()
                assert isinstance(app.screen, NetWorthHistoryScreen)
                label = app.screen.query_one("#error-label", Label)
                assert label.display is True

        asyncio.run(_run())

    def test_default_status_scope_is_historical(self) -> None:
        months = _make_months((2025, 1), (2025, 2))
        rows = [
            HistoryAggregationRow(Month(2025, 1), "asset", "asset", 100_000, "USD"),
        ]
        result = _make_history_result(months, rows)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")  # Net Worth History
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, NetWorthHistoryScreen)
                assert screen._status_scope == AccountStatusScope.HISTORICAL

        asyncio.run(_run())

    def test_scope_selector_widget_is_present(self) -> None:
        from textual.widgets import RadioSet

        months = _make_months((2025, 1), (2025, 2))
        rows = [
            HistoryAggregationRow(Month(2025, 1), "asset", "asset", 100_000, "USD"),
        ]
        result = _make_history_result(months, rows)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")  # Net Worth History
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, NetWorthHistoryScreen)
                selector = screen.query_one("#scope-selector", RadioSet)
                assert selector is not None

        asyncio.run(_run())

    def test_scope_change_to_active_updates_status_scope(self) -> None:
        from textual.widgets import RadioButton, RadioSet

        months = _make_months((2025, 1), (2025, 2))
        rows = [
            HistoryAggregationRow(Month(2025, 1), "asset", "asset", 100_000, "USD"),
        ]
        result = _make_history_result(months, rows)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")  # Net Worth History
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, NetWorthHistoryScreen)
                radio_set = screen.query_one("#scope-selector", RadioSet)
                active_btn = screen.query_one("#scope-active", RadioButton)
                radio_set.post_message(RadioSet.Changed(radio_set, active_btn))
                await pilot.pause()
                assert screen._status_scope == AccountStatusScope.ACTIVE

        asyncio.run(_run())

    def test_scope_change_to_all_updates_status_scope(self) -> None:
        from textual.widgets import RadioButton, RadioSet

        months = _make_months((2025, 1), (2025, 2))
        rows = [
            HistoryAggregationRow(Month(2025, 1), "asset", "asset", 100_000, "USD"),
        ]
        result = _make_history_result(months, rows)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")  # Net Worth History
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, NetWorthHistoryScreen)
                radio_set = screen.query_one("#scope-selector", RadioSet)
                all_btn = screen.query_one("#scope-all", RadioButton)
                radio_set.post_message(RadioSet.Changed(radio_set, all_btn))
                await pilot.pause()
                assert screen._status_scope == AccountStatusScope.ALL

        asyncio.run(_run())

    def test_scope_change_preserves_start_and_end_month(self) -> None:
        from textual.widgets import RadioButton, RadioSet

        months = _make_months((2025, 1), (2025, 2), (2025, 3))
        rows = [HistoryAggregationRow(Month(2025, 1), "asset", "asset", 100_000, "USD")]
        result = _make_history_result(months, rows)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")  # Net Worth History
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, NetWorthHistoryScreen)

                # Pin non-default start/end months
                screen._start_month = months[0]
                screen._end_month = months[1]

                # Change scope
                radio_set = screen.query_one("#scope-selector", RadioSet)
                active_btn = screen.query_one("#scope-active", RadioButton)
                radio_set.post_message(RadioSet.Changed(radio_set, active_btn))
                await pilot.pause()

                # Pinned dates must survive the scope change
                assert screen._start_month == months[0]
                assert screen._end_month == months[1]

        asyncio.run(_run())

    def test_show_error_makes_label_visible_and_clears_table(self) -> None:
        from textual.widgets import DataTable, Label

        months = _make_months((2025, 1), (2025, 2))
        rows = [
            HistoryAggregationRow(Month(2025, 1), "asset", "asset", 100_000, "USD"),
            HistoryAggregationRow(Month(2025, 1), "liability", "liability", 40_000, "USD"),  # noqa: E501
        ]
        result = _make_history_result(months, rows)
        app = _make_app(months, result)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("down")  # Reports
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("enter")  # Net Worth History
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, NetWorthHistoryScreen)
                screen._show_error("Mixed currencies")
                label = screen.query_one("#error-label", Label)
                assert label.display is True
                table = screen.query_one("#history-table", DataTable)
                assert table.row_count == 0

        asyncio.run(_run())
