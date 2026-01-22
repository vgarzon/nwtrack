"""
Tests for account creator use case
"""

import re

import pytest

import nwtrack.application.use_cases.create_account
from nwtrack.application.use_cases.create_account import AccountCreator
from nwtrack.bootstrap.container import Container
from tests.helpers import init_db_tables_w_entities


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.use_cases.create_account import (
        AccountCreator,
        Console,
        FetchService,
    )
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.infra.config.settings import Settings

    return (
        base_container.register(
            DBAdminService,
            lambda c: DBAdminService(
                c.resolve(Settings), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            Console,
            lambda c: Console(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            AccountCreator,
            lambda c: AccountCreator(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                console=c.resolve(Console),
            ),
        )
    )


def test_account_creator_run_success_defaults(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
    capsys,
) -> None:
    # TODO: Use common fixture to init DB with entities
    input_prompt = iter(
        [
            "savings_account_3",  # Account name
            "Savings account in USD",  # Account description
        ]
    )
    input_int_prompt = iter(
        [
            "1",  # Account type (1: asset)
            "1",  # Currency code (0: USD)
            "1",  # Status (0: active)
            "2025",  # Initial year
            "10",  # Initial month
            "100",  # Initial balance
        ]
    )

    def mock_prompt(*args, **kwargs):
        return next(input_prompt)

    def mock_int_prompt(*args, **kwargs):
        return int(next(input_int_prompt))

    init_db_tables_w_entities(configured_container, sample_entities)
    monkeypatch.setattr(
        nwtrack.application.use_cases.create_account.Prompt,
        "ask",
        mock_prompt,
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.create_account.IntPrompt,
        "ask",
        mock_int_prompt,
    )
    configured_container.resolve(AccountCreator).run()
    captured = capsys.readouterr()
    # TODO: Enable assertions through direct database queries
    assert re.search(r"Account created successfully", captured.out)
    assert re.search(r"Account name: savings_account_3", captured.out)
    assert re.search(r"Account ID: 5", captured.out)
    assert re.search(r"Initial month: 2025-10", captured.out)
    assert re.search(r"Initial balance: 100", captured.out)
