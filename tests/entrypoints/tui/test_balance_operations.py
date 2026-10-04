"""Tests for Phase 31 TUI balance operation screens (roll-forward, transfer)."""

import asyncio
from collections.abc import Callable
from unittest.mock import MagicMock

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Input, Select

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.balance_edit import BalanceEditModal
from nwtrack.entrypoints.tui.screens.balance_update import BalanceUpdateScreen
from nwtrack.entrypoints.tui.screens.confirm_modal import ConfirmModal
from nwtrack.entrypoints.tui.screens.roll_forward import RollForwardModal
from nwtrack.entrypoints.tui.screens.transfer import TransferModal, _compute_deltas
from nwtrack.infra.persistence.orm.models import (
    Account,
    Balance,
    Category,
    Side,
    Status,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _month(year: int, month: int) -> Month:
    return Month(year, month)


def _make_category(name: str, side: Side) -> Category:
    return Category(name=name, side=side)


def _make_account(
    id_: int,
    name: str,
    category: Category,
    status: Status = Status.ACTIVE,
) -> Account:
    acc = Account(
        name=name,
        description="",
        category_name=category.name,
        institution_id=None,
        currency_code="USD",
        status=status,
    )
    acc.id = id_
    acc.category = category
    acc.institution = None
    acc.tags = []
    return acc


def _make_uow_factory(
    copy_count: int = 3,
    get_by_account_side_effect=None,
) -> tuple[MagicMock, MagicMock]:
    uow_factory = MagicMock()
    mock_uow = MagicMock()
    uow_factory.return_value.__enter__ = MagicMock(return_value=mock_uow)
    uow_factory.return_value.__exit__ = MagicMock(return_value=False)
    mock_uow.balances.copy_by_month.return_value = copy_count
    if get_by_account_side_effect is not None:
        mock_uow.balances.get_by_account_id.side_effect = get_by_account_side_effect
    else:
        mock_uow.balances.get_by_account_id.side_effect = IndexError
    return uow_factory, mock_uow


def _make_nwtrack_app(months=None) -> NWTrackApp:
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = months or []
    fetcher.get_accounts.return_value = []
    fetcher.get_month_balances.return_value = []
    fetcher.get_networth.return_value = None
    uow_factory, _ = _make_uow_factory()
    return NWTrackApp(fetcher=fetcher, uow=uow_factory)


# Minimal test App wrapper for mounting modals directly.


class _RollForwardTestApp(App):
    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
        source_month: Month,
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow
        self._source_month = source_month

    def compose(self) -> ComposeResult:
        return iter([])

    async def on_mount(self) -> None:
        await self.push_screen(
            RollForwardModal(
                fetcher=self._fetcher,
                uow=self._uow,
                source_month=self._source_month,
            )
        )


class _TransferTestApp(App):
    def __init__(
        self,
        fetcher: FetchService,
        uow: Callable[[], UnitOfWork],
        month: Month,
        from_account_id: int | None = None,
    ) -> None:
        super().__init__()
        self._fetcher = fetcher
        self._uow = uow
        self._month = month
        self._from_account_id = from_account_id

    def compose(self) -> ComposeResult:
        return iter([])

    async def on_mount(self) -> None:
        await self.push_screen(
            TransferModal(
                fetcher=self._fetcher,
                uow=self._uow,
                month=self._month,
                from_account_id=self._from_account_id,
            )
        )


# ── BalanceUpdateScreen threshold warning ──────────────────────────────────────


def _make_balance_update_app(
    current_amount: int,
    change_warning_threshold_pct: float = 20.0,
) -> tuple[NWTrackApp, MagicMock]:
    m = _month(2025, 1)
    cat = _make_category("Checking", Side.ASSET)
    acc = _make_account(1, "Checking", cat)
    balance = Balance(account_id=1, month=m, amount=current_amount)
    balance.account = acc

    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = [m]
    fetcher.get_month_balances.return_value = [balance]
    fetcher.get_networth.return_value = None
    fetcher.get_balance_for_account_id.return_value = balance

    uow_factory, mock_uow = _make_uow_factory()
    app = NWTrackApp(
        fetcher=fetcher,
        uow=uow_factory,
        change_warning_threshold_pct=change_warning_threshold_pct,
    )
    return app, mock_uow


async def _navigate_to_balances_and_open_edit(pilot) -> None:
    await pilot.press("enter")  # Balances (first item)
    await pilot.pause()
    table = pilot.app.screen.query_one("#balance-table", DataTable)
    table.focus()
    await pilot.pause()
    await pilot.press("enter")  # select first row
    await pilot.pause()


async def _submit_edit_amount(pilot, amount: int) -> None:
    assert isinstance(pilot.app.screen, BalanceEditModal)
    pilot.app.screen.query_one("#edit-input", Input).value = str(amount)
    await pilot.press("enter")
    await pilot.pause()


class TestBalanceUpdateThresholdWarning:
    """Warn-and-confirm flow for balance changes above the configured threshold."""

    def test_small_change_writes_without_confirmation(self) -> None:
        app, mock_uow = _make_balance_update_app(current_amount=200)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await _navigate_to_balances_and_open_edit(pilot)
                await _submit_edit_amount(pilot, 210)  # ~5% change
                assert isinstance(pilot.app.screen, BalanceUpdateScreen)

        asyncio.run(_run())
        mock_uow.balances.update.assert_called_once_with(
            account_id=1, month=_month(2025, 1), new_amount=210
        )

    def test_large_change_confirmed_writes_new_amount(self) -> None:
        app, mock_uow = _make_balance_update_app(current_amount=200)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await _navigate_to_balances_and_open_edit(pilot)
                await _submit_edit_amount(pilot, 300)  # 50% change
                assert isinstance(pilot.app.screen, ConfirmModal)
                await pilot.press("enter")  # confirm button has initial focus
                await pilot.pause()
                assert isinstance(pilot.app.screen, BalanceUpdateScreen)

        asyncio.run(_run())
        mock_uow.balances.update.assert_called_once_with(
            account_id=1, month=_month(2025, 1), new_amount=300
        )

    def test_large_change_declined_reprompts_without_writing(self) -> None:
        app, mock_uow = _make_balance_update_app(current_amount=200)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await _navigate_to_balances_and_open_edit(pilot)
                await _submit_edit_amount(pilot, 300)  # 50% change
                assert isinstance(pilot.app.screen, ConfirmModal)
                await pilot.press("escape")  # decline
                await pilot.pause()
                assert isinstance(pilot.app.screen, BalanceEditModal)
                await _submit_edit_amount(pilot, 205)  # below threshold now
                assert isinstance(pilot.app.screen, BalanceUpdateScreen)

        asyncio.run(_run())
        mock_uow.balances.update.assert_called_once_with(
            account_id=1, month=_month(2025, 1), new_amount=205
        )

    def test_disabled_threshold_never_shows_confirmation(self) -> None:
        app, mock_uow = _make_balance_update_app(
            current_amount=200, change_warning_threshold_pct=0
        )

        async def _run() -> None:
            async with app.run_test() as pilot:
                await _navigate_to_balances_and_open_edit(pilot)
                await _submit_edit_amount(pilot, 10_000)
                assert isinstance(pilot.app.screen, BalanceUpdateScreen)

        asyncio.run(_run())
        mock_uow.balances.update.assert_called_once_with(
            account_id=1, month=_month(2025, 1), new_amount=10_000
        )


# ── BalanceUpdateScreen bindings ──────────────────────────────────────────────


class TestBalanceUpdateScreenBindings:
    """Verify r and t bindings push the correct screens."""

    def test_r_pushes_roll_forward_modal(self) -> None:
        m = _month(2025, 1)
        app = _make_nwtrack_app(months=[m])

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("enter")  # Balances (first item)
                await pilot.pause()
                assert isinstance(app.screen, BalanceUpdateScreen)
                await pilot.press("r")
                await pilot.pause()
                assert isinstance(app.screen, RollForwardModal)
                await pilot.press("escape")
                await pilot.pause()

        asyncio.run(_run())

    def test_t_pushes_transfer_modal(self) -> None:
        m = _month(2025, 1)
        app = _make_nwtrack_app(months=[m])

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("enter")  # Balances (first item)
                await pilot.pause()
                assert isinstance(app.screen, BalanceUpdateScreen)
                await pilot.press("t")
                await pilot.pause()
                assert isinstance(app.screen, TransferModal)
                await pilot.press("escape")
                await pilot.pause()

        asyncio.run(_run())

    def test_t_prefills_from_account_with_highlighted_row(self) -> None:
        m = _month(2025, 1)
        cat = _make_category("Savings", Side.ASSET)
        acc1 = _make_account(1, "A", cat)
        acc2 = _make_account(2, "B", cat)
        b1 = Balance(account_id=1, month=m, amount=10)
        b1.account = acc1
        b2 = Balance(account_id=2, month=m, amount=20)
        b2.account = acc2
        fetcher = MagicMock()
        fetcher.get_recent_months.return_value = [m]
        fetcher.get_month_balances.return_value = [b1, b2]
        fetcher.get_accounts.return_value = [acc1, acc2]
        fetcher.get_networth.return_value = None
        uow_factory, _ = _make_uow_factory()
        app = NWTrackApp(fetcher=fetcher, uow=uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("down")
                await pilot.press("t")
                await pilot.pause()
                modal = app.screen
                assert isinstance(modal, TransferModal)
                assert modal.query_one("#select-from", Select).value == "2"
                assert modal.focused is modal.query_one("#select-to", Select)
                await pilot.press("escape")
                await pilot.pause()

        asyncio.run(_run())

    def test_r_does_nothing_when_no_month_data(self) -> None:
        app = _make_nwtrack_app(months=[])

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("enter")  # Balances (first item)
                await pilot.pause()
                assert isinstance(app.screen, BalanceUpdateScreen)
                await pilot.press("r")
                await pilot.pause()
                assert isinstance(app.screen, BalanceUpdateScreen)

        asyncio.run(_run())


# ── RollForwardModal ──────────────────────────────────────────────────────────


def _make_rf_app(
    source_month: Month,
    latest_month: Month | None = None,
    target_has_balances: bool = False,
    source_has_balances: bool = True,
    copy_count: int = 3,
) -> tuple[_RollForwardTestApp, MagicMock, MagicMock]:
    fetcher = MagicMock()
    fetcher.get_recent_months.return_value = [latest_month] if latest_month else []

    def _check_month(m: Month) -> bool:
        if latest_month and m == latest_month.increment():
            return target_has_balances
        return source_has_balances

    fetcher.check_month_in_balances.side_effect = _check_month

    uow_factory, mock_uow = _make_uow_factory(copy_count=copy_count)
    app = _RollForwardTestApp(
        fetcher=fetcher, uow=uow_factory, source_month=source_month
    )
    return app, uow_factory, mock_uow


class TestRollForwardModal:
    def test_target_month_is_one_after_latest(self) -> None:
        source = _month(2025, 1)
        latest = _month(2025, 2)
        app, _, _ = _make_rf_app(source, latest_month=latest)

        async def _run() -> None:
            async with app.run_test():
                modal = app.screen
                assert isinstance(modal, RollForwardModal)
                assert modal._target_month == _month(2025, 3)

        asyncio.run(_run())

    def test_confirm_calls_copy_by_month(self) -> None:
        source = _month(2025, 1)
        latest = _month(2025, 1)
        app, _, mock_uow = _make_rf_app(
            source, latest_month=latest, source_has_balances=True
        )

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("ctrl+s")
                await pilot.pause()

        asyncio.run(_run())
        mock_uow.balances.copy_by_month.assert_called_once_with(
            _month(2025, 1), _month(2025, 2)
        )

    def test_cancel_does_not_write_data(self) -> None:
        source = _month(2025, 1)
        latest = _month(2025, 1)
        app, _, mock_uow = _make_rf_app(source, latest_month=latest)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("escape")
                await pilot.pause()

        asyncio.run(_run())
        mock_uow.balances.copy_by_month.assert_not_called()

    def test_confirm_blocked_when_target_has_balances(self) -> None:
        source = _month(2025, 1)
        latest = _month(2025, 2)
        app, _, mock_uow = _make_rf_app(
            source, latest_month=latest, target_has_balances=True
        )

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("ctrl+s")
                await pilot.pause()

        asyncio.run(_run())
        mock_uow.balances.copy_by_month.assert_not_called()

    def test_confirm_blocked_when_no_balance_data(self) -> None:
        source = _month(2025, 1)
        app, _, mock_uow = _make_rf_app(source, latest_month=None)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("ctrl+s")
                await pilot.pause()

        asyncio.run(_run())
        mock_uow.balances.copy_by_month.assert_not_called()

    def test_confirm_blocked_when_source_has_no_balances(self) -> None:
        source = _month(2024, 6)
        latest = _month(2025, 1)
        app, _, mock_uow = _make_rf_app(
            source, latest_month=latest, source_has_balances=False
        )

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("ctrl+s")
                await pilot.pause()

        asyncio.run(_run())
        mock_uow.balances.copy_by_month.assert_not_called()


# ── TransferModal ─────────────────────────────────────────────────────────────


def _make_tr_app(
    accounts: list[Account],
    month: Month,
    get_by_account_side_effect=None,
    from_account_id: int | None = None,
) -> tuple[_TransferTestApp, MagicMock, MagicMock]:
    fetcher = MagicMock()
    fetcher.get_accounts.return_value = accounts
    fetcher.get_recent_months.return_value = [month]

    uow_factory, mock_uow = _make_uow_factory(
        get_by_account_side_effect=get_by_account_side_effect
    )
    app = _TransferTestApp(
        fetcher=fetcher,
        uow=uow_factory,
        month=month,
        from_account_id=from_account_id,
    )
    return app, uow_factory, mock_uow


class TestTransferModal:
    def test_from_account_prefilled_and_to_focused(self) -> None:
        cat = _make_category("Savings", Side.ASSET)
        acc1 = _make_account(1, "A", cat)
        acc2 = _make_account(2, "B", cat)
        app, _, _ = _make_tr_app([acc1, acc2], _month(2025, 1), from_account_id=2)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.pause()
                modal = app.screen
                assert isinstance(modal, TransferModal)
                assert modal.query_one("#select-from", Select).value == "2"
                assert modal.focused is modal.query_one("#select-to", Select)

        asyncio.run(_run())

    def test_no_from_account_keeps_from_empty_and_focused(self) -> None:
        cat = _make_category("Savings", Side.ASSET)
        acc1 = _make_account(1, "A", cat)
        app, _, _ = _make_tr_app([acc1], _month(2025, 1))

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.pause()
                modal = app.screen
                assert isinstance(modal, TransferModal)
                assert modal.query_one("#select-from", Select).value is Select.NULL
                assert modal.focused is modal.query_one("#select-from", Select)

        asyncio.run(_run())

    def test_cancel_does_not_write_data(self) -> None:
        cat = _make_category("Savings", Side.ASSET)
        acc1 = _make_account(1, "A", cat)
        acc2 = _make_account(2, "B", cat)
        app, _, mock_uow = _make_tr_app([acc1, acc2], _month(2025, 1))

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("escape")
                await pilot.pause()

        asyncio.run(_run())
        mock_uow.balances.update.assert_not_called()
        mock_uow.balances.insert.assert_not_called()

    def test_same_account_rejected(self) -> None:
        cat = _make_category("Savings", Side.ASSET)
        acc1 = _make_account(1, "A", cat)
        acc2 = _make_account(2, "B", cat)
        app, _, mock_uow = _make_tr_app([acc1, acc2], _month(2025, 1))

        async def _run() -> None:
            async with app.run_test() as pilot:
                modal = app.screen
                assert isinstance(modal, TransferModal)
                modal.query_one("#select-from", Select).value = "1"
                modal.query_one("#select-to", Select).value = "1"
                modal.query_one("#input-amount", Input).value = "1000"
                await pilot.press("ctrl+s")
                await pilot.pause()

        asyncio.run(_run())
        mock_uow.balances.update.assert_not_called()
        mock_uow.balances.insert.assert_not_called()

    def test_zero_amount_rejected(self) -> None:
        cat = _make_category("Savings", Side.ASSET)
        acc1 = _make_account(1, "A", cat)
        acc2 = _make_account(2, "B", cat)
        app, _, mock_uow = _make_tr_app([acc1, acc2], _month(2025, 1))

        async def _run() -> None:
            async with app.run_test() as pilot:
                modal = app.screen
                assert isinstance(modal, TransferModal)
                modal.query_one("#select-from", Select).value = "1"
                modal.query_one("#select-to", Select).value = "2"
                modal.query_one("#input-amount", Input).value = "0"
                await pilot.press("ctrl+s")
                await pilot.pause()

        asyncio.run(_run())
        mock_uow.balances.update.assert_not_called()
        mock_uow.balances.insert.assert_not_called()

    def test_asset_to_asset_existing_balances(self) -> None:
        cat = _make_category("Savings", Side.ASSET)
        acc1 = _make_account(1, "A", cat)
        acc2 = _make_account(2, "B", cat)
        m = _month(2025, 1)
        bal1 = Balance(account_id=1, month=m, amount=5000)
        bal2 = Balance(account_id=2, month=m, amount=3000)

        def _get_bal(month: Month, account_id: int) -> Balance:
            return bal1 if account_id == 1 else bal2

        app, _, mock_uow = _make_tr_app(
            [acc1, acc2], m, get_by_account_side_effect=_get_bal
        )

        async def _run() -> None:
            async with app.run_test() as pilot:
                modal = app.screen
                assert isinstance(modal, TransferModal)
                modal.query_one("#select-from", Select).value = "1"
                modal.query_one("#select-to", Select).value = "2"
                modal.query_one("#input-amount", Input).value = "1000"
                await pilot.press("ctrl+s")
                await pilot.pause()

        asyncio.run(_run())
        # ASSET → ASSET: from = 5000 + (-1000) = 4000; to = 3000 + 1000 = 4000
        mock_uow.balances.update.assert_any_call(1, m, 4000)
        mock_uow.balances.update.assert_any_call(2, m, 4000)

    def test_asset_to_liability_reduces_both(self) -> None:
        asset_cat = _make_category("Savings", Side.ASSET)
        liab_cat = _make_category("Debt", Side.LIABILITY)
        acc1 = _make_account(1, "A", asset_cat)
        acc2 = _make_account(2, "B", liab_cat)
        m = _month(2025, 1)
        bal1 = Balance(account_id=1, month=m, amount=5000)
        bal2 = Balance(account_id=2, month=m, amount=2000)

        def _get_bal(month: Month, account_id: int) -> Balance:
            return bal1 if account_id == 1 else bal2

        app, _, mock_uow = _make_tr_app(
            [acc1, acc2], m, get_by_account_side_effect=_get_bal
        )

        async def _run() -> None:
            async with app.run_test() as pilot:
                modal = app.screen
                assert isinstance(modal, TransferModal)
                modal.query_one("#select-from", Select).value = "1"
                modal.query_one("#select-to", Select).value = "2"
                modal.query_one("#input-amount", Input).value = "500"
                await pilot.press("ctrl+s")
                await pilot.pause()

        asyncio.run(_run())
        # ASSET → LIABILITY: from = 5000 - 500 = 4500; to = 2000 - 500 = 1500
        mock_uow.balances.update.assert_any_call(1, m, 4500)
        mock_uow.balances.update.assert_any_call(2, m, 1500)

    def test_missing_balance_inserts_new_record(self) -> None:
        cat = _make_category("Savings", Side.ASSET)
        acc1 = _make_account(1, "A", cat)
        acc2 = _make_account(2, "B", cat)
        m = _month(2025, 1)
        bal1 = Balance(account_id=1, month=m, amount=5000)

        def _get_bal(month: Month, account_id: int) -> Balance:
            if account_id == 1:
                return bal1
            raise IndexError  # account 2 has no balance

        app, _, mock_uow = _make_tr_app(
            [acc1, acc2], m, get_by_account_side_effect=_get_bal
        )

        async def _run() -> None:
            async with app.run_test() as pilot:
                modal = app.screen
                assert isinstance(modal, TransferModal)
                modal.query_one("#select-from", Select).value = "1"
                modal.query_one("#select-to", Select).value = "2"
                modal.query_one("#input-amount", Input).value = "1000"
                await pilot.press("ctrl+s")
                await pilot.pause()

        asyncio.run(_run())
        # from account updated
        mock_uow.balances.update.assert_called_once_with(1, m, 4000)
        # to account inserted (was missing → delta = +1000)
        mock_uow.balances.insert.assert_called_once()
        inserted: Balance = mock_uow.balances.insert.call_args[0][0]
        assert inserted.account_id == 2
        assert inserted.amount == 1000


# ── _compute_deltas unit tests ────────────────────────────────────────────────


class TestComputeDeltas:
    def _acc(self, side: Side) -> Account:
        cat = _make_category("x", side)
        return _make_account(1, "x", cat)

    def test_asset_to_asset(self) -> None:
        assert _compute_deltas(self._acc(Side.ASSET), self._acc(Side.ASSET), 100) == (
            -100,
            +100,
        )

    def test_asset_to_liability(self) -> None:
        assert _compute_deltas(
            self._acc(Side.ASSET), self._acc(Side.LIABILITY), 100
        ) == (-100, -100)

    def test_liability_to_asset(self) -> None:
        assert _compute_deltas(
            self._acc(Side.LIABILITY), self._acc(Side.ASSET), 100
        ) == (+100, +100)

    def test_liability_to_liability(self) -> None:
        assert _compute_deltas(
            self._acc(Side.LIABILITY), self._acc(Side.LIABILITY), 100
        ) == (+100, -100)


class TestBalanceUpdateTableWidthAfterTransfer:
    """Regression: columns must not be truncated after the transfer modal closes."""

    def test_columns_fit_content_after_transfer_modal_closes(self) -> None:
        m = _month(2025, 1)
        cat = _make_category("a-rather-long-category-name", Side.ASSET)
        acc = _make_account(1, "A-rather-long-account-name", cat)
        balance = Balance(account_id=1, month=m, amount=1000)
        balance.account = acc

        fetcher = MagicMock()
        fetcher.get_recent_months.return_value = [m]
        acc2 = _make_account(2, "Other", cat)
        balance2 = Balance(account_id=2, month=m, amount=5)
        balance2.account = acc2
        fetcher.get_month_balances.return_value = [balance, balance2]
        fetcher.get_networth.return_value = None
        uow_factory, _ = _make_uow_factory()
        app = NWTrackApp(fetcher=fetcher, uow=uow_factory)

        async def _run() -> None:
            async with app.run_test() as pilot:
                await pilot.press("enter")
                await pilot.pause()
                await pilot.press("t")
                await pilot.pause()
                assert isinstance(app.screen, TransferModal)
                await pilot.press("escape")
                await pilot.pause()
                await pilot.pause()
                assert "A-rather-long-account-name" in app.export_screenshot()

        asyncio.run(_run())
