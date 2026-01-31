"""
Test suite for the roll balances forward use case
"""

import re

import pytest
from tests.helpers import init_db_tables_w_entities

import nwtrack.application.use_cases.roll_balances_forward
from nwtrack.application.use_cases.roll_balances_forward import RollBalancesUpdater
from nwtrack.bootstrap.container import Container, Lifetime


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.data_loader import InitDataService
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.services.fetch import FetchService
    from nwtrack.application.use_cases.roll_balances_forward import Console
    from nwtrack.infra.config.settings import Settings

    return (
        base_container.register(
            DBAdminService,
            lambda c: DBAdminService(
                c.resolve(Settings), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(Console, lambda c: Console(), lifetime=Lifetime.SINGLETON)
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            RollBalancesUpdater,
            lambda c: RollBalancesUpdater(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                console=c.resolve(Console),
            ),
        )
    )


def test_roll_balances_run_defaults(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    """Test initializing database and loading sample data."""
    # TODO: Use common fixture to init DB with entities
    input_confirm = iter(["y"])
    input_prompt = iter(["1"])

    def mock_confirm(question, **kwargs):
        return next(input_confirm)

    def mock_prompt(question, **kwargs):
        return next(input_prompt)

    init_db_tables_w_entities(configured_container, sample_entities)
    monkeypatch.setattr(
        nwtrack.application.use_cases.roll_balances_forward.Confirm,
        "ask",
        mock_confirm,
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.roll_balances_forward.Prompt,
        "ask",
        mock_prompt,
    )
    configured_container.resolve(RollBalancesUpdater).run()
    captured = capsys.readouterr()
    assert re.search(r"Next available .+ month: 2025-12", captured.out)
    assert re.search(r"Rolling balances forward.+from 2025-11 to 2025-12", captured.out)
    assert re.search(r"700.+600.+100", captured.out)
