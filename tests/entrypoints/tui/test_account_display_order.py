"""TUI tests for account display order, hidden accounts and visible totals."""

import asyncio
from unittest.mock import MagicMock

from textual.widgets import DataTable, Label

from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.account_order import AccountOrderScreen
from nwtrack.entrypoints.tui.screens.accounts import AccountsListScreen
from nwtrack.entrypoints.tui.screens.admin_menu import AdminMenuScreen
from nwtrack.entrypoints.tui.screens.balance_update import BalanceUpdateScreen
from nwtrack.entrypoints.tui.screens.transfer import TransferModal
from nwtrack.infra.persistence.orm.models import (
    Account,
    Balance,
    Category,
    Side,
    Status,
)

_MONTH = Month(2025, 1)
_ASSET = Category(name="checking", side=Side.ASSET)
_LIAB = Category(name="card", side=Side.LIABILITY)


def _account(
    id_: int,
    name: str,
    category: Category = _ASSET,
    currency: str = "USD",
    hidden: bool = False,
) -> Account:
    acc = Account(
        name=name,
        description="",
        category_name=category.name,
        currency_code=currency,
        status=Status.ACTIVE,
        display_order=id_,
        is_hidden=hidden,
    )
    acc.id = id_
    acc.category = category
    acc.institution = None
    acc.tags = []
    return acc


def _balance(account: Account, amount: int) -> Balance:
    balance = Balance(account_id=account.id, month=_MONTH, amount=amount)
    balance.account = account
    return balance


def _uow() -> tuple[MagicMock, MagicMock]:
    factory = MagicMock()
    mock_uow = MagicMock()
    factory.return_value.__enter__ = MagicMock(return_value=mock_uow)
    factory.return_value.__exit__ = MagicMock(return_value=False)
    return factory, mock_uow


def _label_text(screen, selector: str) -> str:
    return str(screen.query_one(selector, Label).render())


def _row_keys(screen, selector: str) -> list[str]:
    table = screen.query_one(selector, DataTable)
    return [row.value for row in table.rows]


# ── AccountOrderScreen ───────────────────────────────────────────────────────


class TestAccountOrderScreen:
    def _app(self, accounts):
        fetcher = MagicMock()
        fetcher.get_recent_months.return_value = []
        fetcher.get_accounts.return_value = accounts
        uow_factory, mock_uow = _uow()
        return NWTrackApp(fetcher=fetcher, uow=uow_factory), fetcher, mock_uow

    def test_lists_all_accounts_including_hidden(self) -> None:
        accounts = [_account(1, "a"), _account(2, "b", hidden=True)]
        app, fetcher, _ = self._app(accounts)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await app.push_screen(AccountOrderScreen(fetcher, app._uow))
                await pilot.pause()
                assert _row_keys(app.screen, "#order-table") == ["1", "2"]
                fetcher.get_accounts.assert_called_with(
                    active_only=False, include_hidden=True
                )

        asyncio.run(_run())

    def test_move_down_and_up_call_repository_and_cursor_follows(self) -> None:
        a, b = _account(1, "a"), _account(2, "b")
        app, fetcher, mock_uow = self._app([a, b])

        async def _run() -> None:
            async with app.run_test() as pilot:
                await app.push_screen(AccountOrderScreen(fetcher, app._uow))
                await pilot.pause()
                mock_uow.accounts.move.return_value = True
                fetcher.get_accounts.return_value = [b, a]  # order after the move
                await pilot.press("d")
                await pilot.pause()
                mock_uow.accounts.move.assert_called_with(1, 1)
                table = app.screen.query_one("#order-table", DataTable)
                assert _row_keys(app.screen, "#order-table") == ["2", "1"]
                assert table.cursor_row == 1  # cursor stays on moved account

                fetcher.get_accounts.return_value = [a, b]
                await pilot.press("u")
                await pilot.pause()
                mock_uow.accounts.move.assert_called_with(1, -1)
                assert table.cursor_row == 0

        asyncio.run(_run())

    def test_toggle_hidden_flips_flag(self) -> None:
        a, b = _account(1, "a"), _account(2, "b", hidden=True)
        app, fetcher, mock_uow = self._app([a, b])

        async def _run() -> None:
            async with app.run_test() as pilot:
                await app.push_screen(AccountOrderScreen(fetcher, app._uow))
                await pilot.pause()
                await pilot.press("h")  # row 0: visible -> hidden
                mock_uow.accounts.set_hidden.assert_called_with(1, True)
                await pilot.press("down")
                await pilot.press("h")  # row 1: hidden -> visible
                mock_uow.accounts.set_hidden.assert_called_with(2, False)

        asyncio.run(_run())

    def test_reachable_from_admin_menu(self) -> None:
        fetcher = MagicMock()
        fetcher.get_recent_months.return_value = []
        fetcher.get_accounts.return_value = []
        uow_factory, _ = _uow()
        app = NWTrackApp(fetcher=fetcher, uow=uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await app.push_screen(AdminMenuScreen(fetcher, uow_factory))
                await pilot.pause()
                for _ in range(3):
                    await pilot.press("down")
                await pilot.press("enter")
                await pilot.pause()
                assert isinstance(app.screen, AccountOrderScreen)

        asyncio.run(_run())


# ── BalanceUpdateScreen ──────────────────────────────────────────────────────


class TestBalanceUpdateHiddenToggle:
    def _app(self):
        checking = _account(1, "checking")
        card = _account(2, "card", category=_LIAB)
        hidden = _account(3, "old", hidden=True)
        euro = _account(4, "euro", currency="EUR")
        everything = [
            _balance(checking, 1000),
            _balance(card, 300),
            _balance(hidden, 50),
            _balance(euro, 70),
        ]
        fetcher = MagicMock()
        fetcher.get_recent_months.return_value = [_MONTH]
        fetcher.get_networth.return_value = None

        def _month_balances(month, active_only=True, include_hidden=True):
            return [b for b in everything if include_hidden or not b.account.is_hidden]

        fetcher.get_month_balances.side_effect = _month_balances
        uow_factory, _ = _uow()
        return NWTrackApp(fetcher=fetcher, uow=uow_factory), fetcher, uow_factory

    def test_hidden_rows_absent_by_default_and_toggle_shows_them(self) -> None:
        app, fetcher, uow_factory = self._app()

        async def _run() -> None:
            async with app.run_test() as pilot:
                await app.push_screen(BalanceUpdateScreen(fetcher, uow_factory))
                await pilot.pause()
                screen = app.screen
                assert _row_keys(screen, "#balance-table") == ["1", "2", "4"]
                await pilot.press("h")
                await pilot.pause()
                assert _row_keys(screen, "#balance-table") == ["1", "2", "3", "4"]
                await pilot.press("h")
                await pilot.pause()
                assert _row_keys(screen, "#balance-table") == ["1", "2", "4"]

        asyncio.run(_run())

    def test_visible_total_follows_toggle_and_nets_liabilities_per_currency(
        self,
    ) -> None:
        app, fetcher, uow_factory = self._app()

        async def _run() -> None:
            async with app.run_test() as pilot:
                await app.push_screen(BalanceUpdateScreen(fetcher, uow_factory))
                await pilot.pause()
                screen = app.screen
                text = _label_text(screen, "#visible-total-label")
                assert "700" in text and "USD" in text  # 1000 - 300
                assert "70" in text and "EUR" in text
                assert "incl. hidden" not in text
                await pilot.press("h")
                await pilot.pause()
                text = _label_text(screen, "#visible-total-label")
                assert "750" in text  # 1000 - 300 + 50
                assert "incl. hidden" in text

        asyncio.run(_run())

    def test_networth_label_is_unaffected_by_toggle(self) -> None:
        app, fetcher, uow_factory = self._app()

        async def _run() -> None:
            async with app.run_test() as pilot:
                await app.push_screen(BalanceUpdateScreen(fetcher, uow_factory))
                await pilot.pause()
                await pilot.press("h")
                await pilot.pause()
                # Net worth always comes from the unfiltered service call.
                fetcher.get_networth.assert_called_with(_MONTH, "USD")

        asyncio.run(_run())


# ── AccountsListScreen / TransferModal ───────────────────────────────────────


def test_accounts_list_toggle_shows_hidden_accounts() -> None:
    visible, hidden = _account(1, "a"), _account(2, "b", hidden=True)
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = []
    fetcher.get_all_categories.return_value = []
    fetcher.get_accounts.side_effect = lambda active_only=True, include_hidden=True: [
        a for a in (visible, hidden) if include_hidden or not a.is_hidden
    ]
    uow_factory, _ = _uow()
    app = NWTrackApp(fetcher=fetcher, uow=uow_factory)

    async def _run() -> None:
        async with app.run_test() as pilot:
            await app.push_screen(AccountsListScreen(fetcher, uow_factory))
            await pilot.pause()
            assert _row_keys(app.screen, "#accounts-table") == ["1"]
            await pilot.press("h")
            await pilot.pause()
            assert _row_keys(app.screen, "#accounts-table") == ["1", "2"]

    asyncio.run(_run())


def _transfer_accounts(from_account_id: int | None) -> list[int]:
    accounts = [_account(1, "a"), _account(2, "b", hidden=True), _account(3, "c")]
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = []
    fetcher.get_accounts.return_value = accounts
    uow_factory, _ = _uow()
    app = NWTrackApp(fetcher=fetcher, uow=uow_factory)
    shown: list[int] = []

    async def _run() -> None:
        async with app.run_test() as pilot:
            modal = TransferModal(
                fetcher=fetcher,
                uow=uow_factory,
                month=_MONTH,
                from_account_id=from_account_id,
            )
            await app.push_screen(modal)
            await pilot.pause()
            shown.extend(a.id for a in modal._accounts)

    asyncio.run(_run())
    return shown


def test_transfer_modal_omits_hidden_accounts() -> None:
    assert _transfer_accounts(None) == [1, 3]


def test_transfer_modal_keeps_hidden_prefilled_from_account() -> None:
    assert _transfer_accounts(2) == [1, 2, 3]
