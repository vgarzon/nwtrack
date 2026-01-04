"""
Test suite for the roll balances forward use case
"""

import re
import pytest
from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.config import Config
from nwtrack.container import Container
from nwtrack.dbmanager import DBConnectionManager
from nwtrack.services import InitDataService
from nwtrack.unitofwork import UnitOfWork
from nwtrack.use_cases.roll_balances_forward import RollBalancesUpdater
from tests.helpers import init_db_tables_w_entities


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    return (
        base_container.register(
            DBAdminService,
            lambda c: SQLiteAdminService(
                c.resolve(Config), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            RollBalancesUpdater,
            lambda c: RollBalancesUpdater(uow=lambda: c.resolve(UnitOfWork)),
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
    init_db_tables_w_entities(configured_container, sample_entities)
    inputs = iter(
        [
            "",  # Enter
            "Y",  # Accept default source month
        ]
    )
    updater: RollBalancesUpdater = configured_container.resolve(RollBalancesUpdater)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    updater.run()
    captured = capsys.readouterr()
    assert re.search(r"Next available .+ month: 2025-12", captured.out)
    assert re.search(r"Net Worth: 100", captured.out)
