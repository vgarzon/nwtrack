"""
Tests for account creator use case
"""

import re
import pytest
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.infra.config.settings import Settings
from nwtrack.bootstrap.container import Container
from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.use_cases.create_account import AccountCreator
from tests.helpers import init_db_tables_w_entities


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    return base_container.register(
        DBAdminService,
        lambda c: DBAdminService(c.resolve(Settings), c.resolve(DBConnectionManager)),
    ).register(
        AccountCreator,
        lambda c: AccountCreator(uow=lambda: c.resolve(UnitOfWork)),
    )


def test_account_creator_run_success(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    # TODO: Use common fixture to init DB with entities
    init_db_tables_w_entities(configured_container, sample_entities)
    inputs = iter(
        [
            "savings_account_3",  # Account name
            "Savings account in USD",  # Account description
            "1",  # Account type (1: asset)
            "0",  # Currency code (0: USD)
            "0",  # Status (0: active)
            "2025 10",  # Initial month
            "100",  # Initial balance
        ]
    )
    updater: AccountCreator = configured_container.resolve(AccountCreator)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    updater.run()
    captured = capsys.readouterr()
    print(captured.out)
    assert re.search(r"Inserted account with ID 5", captured.out)
    assert re.search(r"Inserted one balance with ID 43", captured.out)
    assert re.search(r"Account 'savings_account_3' created successfully", captured.out)
