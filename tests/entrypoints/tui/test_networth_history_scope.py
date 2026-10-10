"""Real-database test: the status scope selector changes NetWorthHistoryScreen rows."""

import asyncio

from tests.helpers import _uow_factory, init_db_tables_w_entities
from textual.widgets import DataTable, Select

from nwtrack.application.dto import AccountStatusScope
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.tui.app import NWTrackApp
from nwtrack.entrypoints.tui.screens.networth_history import NetWorthHistoryScreen
from nwtrack.infra.persistence.orm.models import (
    AccountStatusHistory,
    Balance,
    Status,
)


def test_scope_selector_changes_rows(base_container, sample_entities) -> None:
    container = build_data_services_container(base_container)
    init_db_tables_w_entities(container, sample_entities)
    jan, feb = Month(2026, 1), Month(2026, 2)
    with _uow_factory(container) as uow:
        ash = AccountStatusHistory
        uow.account_status_history.insert_many(
            [
                ash(account_id=1, status=Status.ACTIVE, effective_month=jan),
                ash(account_id=1, status=Status.INACTIVE, effective_month=feb),
                ash(account_id=2, status=Status.ACTIVE, effective_month=jan),
            ]
        )
        uow.balances.insert(Balance(account_id=1, month=jan, amount=100))
        uow.balances.insert(Balance(account_id=1, month=feb, amount=200))
        uow.balances.insert(Balance(account_id=2, month=jan, amount=300))
        uow.balances.insert(Balance(account_id=2, month=feb, amount=400))
        acc = uow.accounts.get_by_id(1)
        assert acc is not None
        acc.status = Status.INACTIVE
        uow.accounts.update(acc)

    def uow_factory() -> UnitOfWork:
        return container.resolve(UnitOfWork)

    fetcher = FetchService(uow=uow_factory)
    app = NWTrackApp(fetcher=fetcher, uow=uow_factory)

    def rows(table: DataTable) -> list[tuple[str, ...]]:
        return [
            tuple(str(getattr(c, "plain", c)) for c in table.get_row_at(i))
            for i in range(table.row_count)
        ]

    async def _run() -> dict[AccountStatusScope, list]:
        out = {}
        async with app.run_test() as pilot:
            await app.push_screen(NetWorthHistoryScreen(fetcher, uow_factory))
            await pilot.pause()
            screen = app.screen
            table = screen.query_one("#history-table", DataTable)
            sel = screen.query_one("#scope-select", Select)
            for scope in AccountStatusScope:
                sel.value = scope
                await pilot.pause()
                out[scope] = rows(table)
        return out

    out = asyncio.run(_run())
    active = out[AccountStatusScope.ACTIVE]
    historical = out[AccountStatusScope.HISTORICAL]
    all_ = out[AccountStatusScope.ALL]
    assert active != historical
    assert historical != all_
    assert active != all_
