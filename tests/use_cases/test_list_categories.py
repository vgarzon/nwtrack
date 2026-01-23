"""
Tests for list categories service
"""

import re

import pytest

from nwtrack.application.use_cases.list_categories import (
    FetchService,
    ListCategories,
)
from nwtrack.bootstrap.container import Container
from nwtrack.infra.config.settings import Settings
from tests.helpers import init_db_tables_w_entities


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""

    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings
    from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory

    console_default = ConsoleSettings(record=True)

    return (
        base_container.register(
            ConsoleFactory,
            lambda _: ConsoleFactory(default_settings=console_default),
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
            ListCategories,
            lambda c: ListCategories(
                fetcher=c.resolve(FetchService),
                console_factory=c.resolve(ConsoleFactory),
            ),
        )
    )


def test_list_accounts_active_only(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    # TODO: Use common fixture to init DB with entities
    init_db_tables_w_entities(configured_container, sample_entities)
    service: ListCategories = configured_container.resolve(ListCategories)
    service.run()
    recorded = service._console.export_text()
    assert re.search(r"Categories", recorded)
    assert re.search(r".+checking.+asset", recorded)
    assert re.search(r".+revolving_credit.+liability", recorded)
