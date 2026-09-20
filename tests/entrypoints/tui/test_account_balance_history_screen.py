"""Tests for AccountBalanceHistoryScreen."""

import asyncio
from unittest.mock import MagicMock

from nwtrack.domain.models import Account, Balance, Status
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.account_balance_history import (
    AccountBalanceHistoryScreen,
)
from nwtrack.entrypoints.tui.screens.reports_menu import ReportsMenuScreen


def _account(account_id: int, name: str) -> Account:
    account = Account(
        name=name,
        description="",
        category_name="checking",
        currency_code="USD",
        status=Status.ACTIVE,
    )
    account.id = account_id
    return account


def _balance(account_id: int, month: Month, amount: int) -> Balance:
    return Balance(account_id=account_id, month=month, amount=amount)


def _make_app(
    accounts: list[Account],
    balances: list[Balance],
) -> NWTrackApp:
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = []
    fetcher.get_available_aggregation_months.return_value = []
    fetcher.get_accounts.return_value = accounts
    fetcher.get_balances_for_account.return_value = balances

    accounts_by_id = {account.id: account for account in accounts}
    balances_by_account: dict[int, list[Balance]] = {}
    for balance in balances:
        balances_by_account.setdefault(balance.account_id, []).append(balance)

    mock_uow = MagicMock()
    mock_uow.accounts.get_by_id.side_effect = lambda aid: accounts_by_id.get(aid)
    mock_uow.balances.get_all_by_account_id.side_effect = (
        lambda aid: balances_by_account.get(aid, [])
    )

    uow_factory = MagicMock()
    uow_factory.return_value.__enter__ = MagicMock(return_value=mock_uow)
    uow_factory.return_value.__exit__ = MagicMock(return_value=False)

    return NWTrackApp(fetcher=fetcher, uow=uow_factory)


async def _open_screen(pilot) -> None:
    await pilot.press("down")  # Reports
    await pilot.press("enter")
    await pilot.pause()
    await pilot.press("down")  # Aggregation
    await pilot.press("down")  # Account History
    await pilot.press("enter")
    await pilot.pause()


class TestAccountBalanceHistoryScreenNavigation:
    def test_screen_pushes_from_reports_menu(self) -> None:
        accounts = [_account(1, "bank_1_checking")]
        balances = [_balance(1, Month(2025, 1), 100)]
        app = _make_app(accounts, balances)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await _open_screen(pilot)
                assert isinstance(app.screen, AccountBalanceHistoryScreen)

        asyncio.run(_run())

    def test_escape_from_screen_pops_to_reports_menu(self) -> None:
        accounts = [_account(1, "bank_1_checking")]
        balances = [_balance(1, Month(2025, 1), 100)]
        app = _make_app(accounts, balances)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await _open_screen(pilot)
                assert isinstance(app.screen, AccountBalanceHistoryScreen)
                await pilot.press("escape")
                await pilot.pause()
                assert isinstance(app.screen, ReportsMenuScreen)

        asyncio.run(_run())

    def test_no_accounts_shows_error(self) -> None:
        app = _make_app(accounts=[], balances=[])

        async def _run() -> None:
            from textual.widgets import Label

            async with app.run_test() as pilot:
                await _open_screen(pilot)
                screen = app.screen
                assert isinstance(screen, AccountBalanceHistoryScreen)
                label = screen.query_one("#error-label", Label)
                assert label.display is True

        asyncio.run(_run())

    def test_no_balances_for_account_shows_error(self) -> None:
        accounts = [_account(1, "bank_1_checking")]
        app = _make_app(accounts, balances=[])

        async def _run() -> None:
            from textual.widgets import Label

            async with app.run_test() as pilot:
                await _open_screen(pilot)
                screen = app.screen
                assert isinstance(screen, AccountBalanceHistoryScreen)
                label = screen.query_one("#error-label", Label)
                assert label.display is True

        asyncio.run(_run())

    def test_default_range_loads_table_and_summary(self) -> None:
        accounts = [_account(1, "bank_1_checking")]
        balances = [
            _balance(1, Month(2025, 1), 100),
            _balance(1, Month(2025, 2), 150),
        ]
        app = _make_app(accounts, balances)

        async def _run() -> None:
            from textual.widgets import DataTable, Label

            async with app.run_test() as pilot:
                await _open_screen(pilot)
                screen = app.screen
                assert isinstance(screen, AccountBalanceHistoryScreen)
                table = screen.query_one("#history-table", DataTable)
                assert table.row_count == 2
                summary = screen.query_one("#summary-label", Label)
                assert "Min: 100" in str(summary.content)
                assert "Max: 150" in str(summary.content)

        asyncio.run(_run())

    def test_changing_account_reloads_table(self) -> None:
        accounts = [
            _account(1, "bank_1_checking"),
            _account(2, "bank_2_savings"),
        ]
        balances = [
            _balance(1, Month(2025, 1), 100),
            _balance(2, Month(2025, 1), 500),
            _balance(2, Month(2025, 2), 600),
        ]
        app = _make_app(accounts, balances)

        async def _run() -> None:
            from textual.widgets import DataTable, Select

            async with app.run_test() as pilot:
                await _open_screen(pilot)
                screen = app.screen
                assert isinstance(screen, AccountBalanceHistoryScreen)
                select = screen.query_one("#account-select", Select)
                select.post_message(Select.Changed(select, "2"))
                await pilot.pause()

                assert screen._account_id == 2
                table = screen.query_one("#history-table", DataTable)
                assert table.row_count == 2

        asyncio.run(_run())

    def test_show_error_makes_label_visible_and_clears_table(self) -> None:
        accounts = [_account(1, "bank_1_checking")]
        balances = [_balance(1, Month(2025, 1), 100)]
        app = _make_app(accounts, balances)

        async def _run() -> None:
            from textual.widgets import DataTable, Label

            async with app.run_test() as pilot:
                await _open_screen(pilot)
                screen = app.screen
                assert isinstance(screen, AccountBalanceHistoryScreen)
                screen._show_error("Something went wrong")
                label = screen.query_one("#error-label", Label)
                assert label.display is True
                table = screen.query_one("#history-table", DataTable)
                assert table.row_count == 0

        asyncio.run(_run())
