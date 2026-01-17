"""
Tests for list accounts service
"""

import re

import pytest

from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.application.use_cases.list_accounts import (
    Console,
    FetchService,
    ListAccounts,
)
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.infra.config.settings import Settings
from tests.helpers import init_db_tables_w_entities


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
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
            ListAccounts,
            lambda c: ListAccounts(
                fetcher=c.resolve(FetchService),
                console=Console(),
            ),
        )
    )


def test_list_accounts_active_only(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    # TODO: Use common fixture to init DB with entities
    init_db_tables_w_entities(configured_container, sample_entities)
    configured_container.resolve(ListAccounts).run(active_only=True)
    captured = capsys.readouterr()
    assert re.search(r".+3.+credit_cards_1.+revolving_credit", captured.out)
    assert re.search(r".+4.+mortgage_1.+mortgage", captured.out) is None


def test_list_all_accounts(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    # TODO: Use common fixture to init DB with entities
    init_db_tables_w_entities(configured_container, sample_entities)
    configured_container.resolve(ListAccounts).run(active_only=False)
    captured = capsys.readouterr()
    assert re.search(r".+3.+credit_cards_1.+revolving_credit", captured.out)
    assert re.search(r".+4.+mortgage_1.+mortgage", captured.out)
