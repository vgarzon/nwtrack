"""
Tests for networth history service
"""

import re

import pytest

from nwtrack.application.use_cases.report_networth_history import (
    Console,
    FetchService,
    NetworthHistoryReport,
)
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.infra.config.settings import Settings
from tests.helpers import init_db_tables_w_entities


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService

    return (
        base_container.register(
            Console,
            lambda c: Console(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            DBAdminService,
            lambda c: DBAdminService(
                c.resolve(Settings), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            NetworthHistoryReport,
            lambda c: NetworthHistoryReport(
                fetcher=c.resolve(FetchService),
                console=c.resolve(Console),
            ),
        )
    )


def test_report_networth_history_default(
    configured_container: Container,
    sample_entities: dict[str, list],
    capsys,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    configured_container.resolve(NetworthHistoryReport).run(n_months=12)
    captured = capsys.readouterr()
    assert len(captured.out.splitlines()) == 18
    assert re.search(r"2024-06 to 2025-11", captured.out)
    assert re.search(r".+2024-06.+2,300.+2,400.+-100.+\s{9}", captured.out)
    assert re.search(r".+2025-11.+700.+600.+100.+-100", captured.out)


def test_report_networth_history_n_months(
    configured_container: Container,
    sample_entities: dict[str, list],
    capsys,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    configured_container.resolve(NetworthHistoryReport).run(n_months=2)
    captured = capsys.readouterr()
    assert len(captured.out.splitlines()) == 8
    assert re.search(r"2025-10 to 2025-11", captured.out)
    assert not re.search(r".+2024-06.+2,300.+2,400.+-100", captured.out)
    assert re.search(r".+2025-10.+900.+700.+200.+\s{9}", captured.out)
    assert re.search(r".+2025-11.+700.+600.+100.+-100", captured.out)
