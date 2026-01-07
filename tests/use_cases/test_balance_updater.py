"""
Test suite for the balance updater use case
"""

import re
import pytest

from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.infra.config.settings import Settings
from nwtrack.bootstrap.container import Container
from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.services import InitDataService
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases.balance_updater import BalanceUpdater
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
    init_db_tables_w_entities(configured_container, sample_entities)
    inputs = iter(
        [
            "2025 11",  # Input month
            "1",  # Update account ID 1
            "300",  # New balance
            "3",  # Update account ID 2
            "500",  # New balance
            "q",  # Quit
        ]
    )
    updater: BalanceUpdater = configured_container.resolve(BalanceUpdater)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    updater.run()
    captured = capsys.readouterr()
    assert re.search(r"Net Worth: 300", captured.out)
