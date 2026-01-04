"""
Test suite for the balance updater use case
"""

import re

from nwtrack.admin import DBAdminService, SQLiteAdminService
from nwtrack.config import Config
from nwtrack.container import Container
from nwtrack.dbmanager import DBConnectionManager
from nwtrack.services import InitDataService
from nwtrack.unitofwork import UnitOfWork
from nwtrack.use_cases.balance_updater import BalanceUpdater
from tests.test_services import init_db_tables_w_entities


def register_services(container: Container) -> Container:
    """Register services in the container."""
    container.register(
        DBAdminService,
        lambda c: SQLiteAdminService(c.resolve(Config), c.resolve(DBConnectionManager)),
    ).register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        BalanceUpdater,
        lambda c: BalanceUpdater(uow=lambda: c.resolve(UnitOfWork)),
    )
    return container


def test_update_balances_run(
    test_container: Container, test_entities: dict[str, list], monkeypatch, capsys
) -> None:
    """Test initializing database and loading sample data."""
    container = register_services(test_container)
    # TODO: Use common fixture to init DB with entities
    init_db_tables_w_entities(container, test_entities)
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
    updater = container.resolve(BalanceUpdater)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    updater.run()
    captured = capsys.readouterr()
    assert re.search(r"Net Worth: 300", captured.out)
