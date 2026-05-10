"""
Tests for networth history service
"""

import re

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.use_cases.report_networth_history import (
    NetworthHistoryReport,
)
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.ui.factory import Console


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.presentation import NetworthHistoryPresenter
    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.services.fetch import FetchService
    from nwtrack.application.use_cases.report_history_aggregation import (
        ReportHistoryAggregation,
    )
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.entrypoints.cli.adapters.report_presenters import (
        RichNetworthHistoryPresenter,
    )
    from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory, ConsoleSettings
    from nwtrack.infra.config.settings import Settings
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    console_default = ConsoleSettings(record=True)

    return (
        base_container.register(
            Console,
            lambda _: ConsoleFactory(console_default)(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            SchemaManager,
            lambda c: SchemaManagerImpl(engine=c.resolve(SQLiteSessionManager).engine),
        )
        .register(
            DBAdminService,
            lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            ReportHistoryAggregation,
            lambda c: ReportHistoryAggregation(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            NetworthHistoryPresenter,
            lambda c: RichNetworthHistoryPresenter(console=c.resolve(Console)),
        )
        .register(
            NetworthHistoryReport,
            lambda c: NetworthHistoryReport(
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(NetworthHistoryPresenter),
                aggregation_report=c.resolve(ReportHistoryAggregation),
            ),
        )
    )


def test_report_networth_history_default(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    configured_container.resolve(NetworthHistoryReport).run(n_months=12)
    captured_out: str = configured_container.resolve(Console).export_text()
    assert len(captured_out.splitlines()) == 25
    assert re.search(r"2024-06 to 2025-11", captured_out)
    assert re.search(r".+2024-06.+2,300.+600.+1,700.+\s{9}", captured_out)
    assert re.search(r".+2025-11.+700.+600.+100.+-100", captured_out)


def test_report_networth_history_n_months(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    configured_container.resolve(NetworthHistoryReport).run(n_months=2)
    captured_out: str = configured_container.resolve(Console).export_text()
    assert len(captured_out.splitlines()) == 15
    assert re.search(r"2025-10 to 2025-11", captured_out)
    assert not re.search(r".+2024-06.+2,300.+600.+1,700", captured_out)
    assert re.search(r".+2025-10.+900.+700.+200.+\s{9}", captured_out)
    assert re.search(r".+2025-11.+700.+600.+100.+-100", captured_out)
    assert re.search(r".+-200.+-100.+-100", captured_out)
