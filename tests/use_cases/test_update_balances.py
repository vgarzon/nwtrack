"""
Test suite for the balance updater use case
"""

import re

import pytest

import nwtrack.application.use_cases.update_balances
from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.application.use_cases.update_balances import BalanceUpdater
from nwtrack.bootstrap.container import Container
from nwtrack.infra.config.settings import Settings
from tests.helpers import init_db_tables_w_entities


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Configure container."""
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
        .register(
            BalanceUpdater,
            lambda c: BalanceUpdater(uow=lambda: c.resolve(UnitOfWork)),
        )
    )


def test_update_balances_run(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    """Test initializing database and loading sample data."""
    # TODO: Use common fixture to init DB with entities
    input_prompt = iter(
        [
            "1",  # Select default month
            "1",  # Select account ID 1
            "3",  # Update account ID 3
            "q",  # Quit
        ]
    )
    input_int_prompt = iter(
        [
            "300",  # New balance for account 1
            "500",  # New balance for account 3
        ]
    )

    def mock_prompt(question, **kwargs):
        return next(input_prompt)

    def mock_int_prompt(question, **kwargs):
        return int(next(input_int_prompt))

    init_db_tables_w_entities(configured_container, sample_entities)
    updater: BalanceUpdater = configured_container.resolve(BalanceUpdater)
    monkeypatch.setattr(
        nwtrack.application.use_cases.update_balances.Prompt,
        "ask",
        mock_prompt,
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.update_balances.IntPrompt,
        "ask",
        mock_int_prompt,
    )
    updater.run()
    captured = capsys.readouterr()
    assert re.search(r"Balances 2025-11", captured.out)
    assert re.search(r"Account bank_1_checking.+2025-11.+200", captured.out)
    assert re.search(r"800.+500.+300", captured.out)

    # TODO: Test other interactions
