"""
Test suite for the forward-fill balances use case
"""

import pytest
from tests.helpers import _uow_factory, init_db_tables_w_entities

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.forward_fill_balances import ForwardFillBalances
from nwtrack.bootstrap.composition import build_data_services_container
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import AccountStatusHistory, Status
from nwtrack.domain.value_objects import Month


@pytest.fixture
def container(base_container: Container, sample_entities) -> Container:
    c = build_data_services_container(base_container)
    c.register(FetchService, lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)))
    init_db_tables_w_entities(c, sample_entities)
    return c


def _filler(container: Container) -> ForwardFillBalances:
    return ForwardFillBalances(
        uow=lambda: container.resolve(UnitOfWork),
        fetcher=container.resolve(FetchService),
    )


def _latest(container: Container) -> Month:
    return container.resolve(FetchService).get_recent_months(1)[0]


def _count(container: Container, month: Month) -> int:
    return container.resolve(FetchService).get_balance_count_for_month(month)


class TestFindGap:
    def test_empty_database_returns_no_gap(self, base_container: Container) -> None:
        c = build_data_services_container(base_container)
        c.register(
            FetchService, lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork))
        )
        from nwtrack.application.services.db_admin import DBAdminService

        c.resolve(DBAdminService).init_database()
        assert _filler(c).find_gap(Month(2026, 10)) == []

    def test_latest_equals_today_returns_no_gap(self, container: Container) -> None:
        latest = _latest(container)
        assert _filler(container).find_gap(latest) == []

    def test_latest_after_today_returns_no_gap(self, container: Container) -> None:
        latest = _latest(container)
        earlier = Month(latest.year - 1, latest.month)
        assert _filler(container).find_gap(earlier) == []

    def test_one_month_gap(self, container: Container) -> None:
        latest = _latest(container)
        assert _filler(container).find_gap(latest.increment()) == [latest.increment()]

    def test_multi_month_gap_ascending(self, container: Container) -> None:
        latest = _latest(container)
        m1 = latest.increment()
        m2 = m1.increment()
        m3 = m2.increment()
        assert _filler(container).find_gap(m3) == [m1, m2, m3]


class TestRun:
    def test_empty_months_is_noop(self, container: Container) -> None:
        result = _filler(container).run([])
        assert result.success
        assert result.data == 0

    def test_multi_month_fill_chains_amounts(self, container: Container) -> None:
        latest = _latest(container)
        m1 = latest.increment()
        m2 = m1.increment()
        expected = _count(container, latest)

        result = _filler(container).run([m1, m2])

        assert result.success
        assert result.data == expected * 2
        with _uow_factory(container) as uow:
            src = {
                b.account_id: b.amount
                for b in uow.balances.get_month(latest, active_only=False)
            }
            filled = {
                b.account_id: b.amount
                for b in uow.balances.get_month(m2, active_only=False)
            }
        assert filled == src

    def test_account_closed_mid_gap_stops_from_closing_month(
        self, container: Container
    ) -> None:
        latest = _latest(container)
        m1 = latest.increment()
        m2 = m1.increment()
        with _uow_factory(container) as uow:
            closed_id = uow.balances.get_month(latest, active_only=False)[0].account_id
            uow.account_status_history.insert(
                AccountStatusHistory(
                    account_id=closed_id,
                    status=Status.INACTIVE,
                    effective_month=m2,
                )
            )

        result = _filler(container).run([m1, m2])

        assert result.success
        with _uow_factory(container) as uow:
            ids_m1 = {b.account_id for b in uow.balances.get_month(m1, False)}
            ids_m2 = {b.account_id for b in uow.balances.get_month(m2, False)}
        assert closed_id in ids_m1
        assert closed_id not in ids_m2

    def test_failure_rolls_back_every_month(self, container: Container) -> None:
        latest = _latest(container)
        m1 = latest.increment()
        m2 = m1.increment()
        # Deactivate every account effective in m2 so the second copy yields zero rows.
        with _uow_factory(container) as uow:
            for b in uow.balances.get_month(latest, active_only=False):
                uow.account_status_history.insert(
                    AccountStatusHistory(
                        account_id=b.account_id,
                        status=Status.INACTIVE,
                        effective_month=m2,
                    )
                )

        result = _filler(container).run([m1, m2])

        assert not result.success
        assert _count(container, m1) == 0
        assert _count(container, m2) == 0
