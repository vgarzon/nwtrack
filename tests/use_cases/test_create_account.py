"""
Tests for account creator use case
"""

import re

import pytest

import nwtrack.application.use_cases.create_account
from nwtrack.application.use_cases.create_account import AccountCreator
from nwtrack.bootstrap.container import Container
from tests.helpers import init_db_tables_w_entities
from nwtrack.domain.value_objects import Month


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.use_cases.create_account import (
        AccountCreator,
        ConsoleFactory,
        FetchService,
    )
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.infra.config.settings import Settings
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings

    console_defaults = ConsoleSettings(record=True)

    return (
        base_container.register(
            DBAdminService,
            lambda c: DBAdminService(
                c.resolve(Settings), c.resolve(DBConnectionManager)
            ),
        )
        .register(
            ConsoleFactory,
            lambda _: ConsoleFactory(default_settings=console_defaults),
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
                console_factory=c.resolve(ConsoleFactory),
            ),
        )
    )


def test_account_creator_run_success_defaults(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    # TODO: Use common fixture to init DB with entities
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        nwtrack.application.use_cases.create_account,
        "prompt_for_account_name",
        lambda *args, **kwargs: "savings_account_3",
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.create_account,
        "prompt_for_account_description",
        lambda *args, **kwargs: "Savings account in USD",
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.create_account,
        "prompt_for_category_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.create_account,
        "prompt_for_currency_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.create_account,
        "prompt_for_status_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.create_account,
        "prompt_for_month",
        lambda *args, **kwargs: Month(2025, 10),
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.create_account,
        "prompt_for_balance_amount",
        lambda *args, **kwargs: 100,
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.create_account,
        "prompt_to_confirm_action",
        lambda *args, **kwargs: True,
    )

    service: AccountCreator = configured_container.resolve(AccountCreator)
    service.run()
    captured_output = service._console.export_text()

    # TODO: Enable assertions through direct database queries

    assert re.search(r"Account created successfully", captured_output)
    assert re.search(r"Account name: savings_account_3", captured_output)
    assert re.search(r"Account ID: 5", captured_output)
    assert re.search(r"Initial month: 2025-10", captured_output)
    assert re.search(r"Initial balance: 100", captured_output)
