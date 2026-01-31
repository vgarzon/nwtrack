"""
Tests for account creator use case
"""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

import nwtrack.entrypoints.cli.adapters.account_presenters
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.create_account import AccountCreator
from nwtrack.bootstrap.container import Container
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.adapters.account_presenters import (
    RichAccountCreationPresenter,
)


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
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
            lambda _: Console(record=True),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            RichAccountCreationPresenter,
            lambda c: RichAccountCreationPresenter(
                console=c.resolve(Console),
                fetcher=c.resolve(FetchService),
            ),
        )
        .register(
            AccountCreator,
            lambda c: AccountCreator(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(RichAccountCreationPresenter),
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

    # Patch the prompt functions in the presenter module
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_for_account_name",
        lambda *args, **kwargs: "savings_account_3",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_for_account_description",
        lambda *args, **kwargs: "Savings account in USD",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_for_category_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_for_currency_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_for_status_choice",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_for_month",
        lambda *args, **kwargs: Month(2025, 10),
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_for_balance_amount",
        lambda *args, **kwargs: 100,
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_to_confirm_action",
        lambda *args, **kwargs: True,
    )

    service: AccountCreator = configured_container.resolve(AccountCreator)
    result = service.run()

    assert result.success
    assert result.data is not None
    account_id, balance_id = result.data
    assert account_id == 5  # Expected new account ID
    assert balance_id > 0  # Balance ID should be positive

    # Check console output
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()

    # TODO: Enable assertions through direct database queries

    assert re.search(r"Account created successfully", captured_output)
    assert re.search(r"Account name: savings_account_3", captured_output)
    assert re.search(r"Account ID: 5", captured_output)
    assert re.search(r"Initial month: 2025-10", captured_output)
    assert re.search(r"Initial balance: 100", captured_output)
