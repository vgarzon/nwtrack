"""
Tests for account creator use case
"""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.update_account_info import UpdateAccountInfo
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.adapters.account_presenters import (
    RichAccountUpdatePresenter,
)


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""

    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.infra.config.settings import Settings
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    return (
        base_container.register(
            SchemaManager,
            lambda c: SchemaManagerImpl(engine=c.resolve(SQLiteSessionManager).engine),
        )
        .register(
            DBAdminService,
            lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
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
            RichAccountUpdatePresenter,
            lambda c: RichAccountUpdatePresenter(
                console=c.resolve(Console),
                fetcher=c.resolve(FetchService),
            ),
        )
        .register(
            UpdateAccountInfo,
            lambda c: UpdateAccountInfo(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(RichAccountUpdatePresenter),
            ),
        )
    )


def test_account_creator_run_success_defaults(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    # TODO: Use common fixture to init DB with entities
    input_prompt = iter(
        [
            "bank_1_savings",  # Account name
            "Savings account at bank 1",  # Account description
        ]
    )
    input_int_prompt = iter(
        [
            "1",  # Account ID
            "2",  # Account type: Savings
            "2",  # Currency: CHF
            "2",  # Status: Inactive
        ]
    )
    input_confirm_prompt = iter(
        [
            True,  # Proceed with update y/n
        ]
    )

    def mock_prompt(*args, **kwargs):
        return next(input_prompt)

    def mock_int_prompt(*args, **kwargs):
        return int(next(input_int_prompt))

    def mock_confirm_prompt(*args, **kwargs):
        return next(input_confirm_prompt)

    init_db_tables_w_entities(configured_container, sample_entities)

    # Patch the prompt methods on the presenter classes
    from rich.prompt import Confirm, IntPrompt, Prompt

    monkeypatch.setattr(
        Prompt,
        "ask",
        mock_prompt,
    )
    monkeypatch.setattr(
        IntPrompt,
        "ask",
        mock_int_prompt,
    )
    monkeypatch.setattr(
        Confirm,
        "ask",
        mock_confirm_prompt,
    )

    from nwtrack.application.dto import OperationResult

    result: OperationResult[None] = configured_container.resolve(
        UpdateAccountInfo
    ).run()

    assert result.success

    # Check console output
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()

    # TODO: Enable assertions through direct database queries
    assert re.search(r"Account ID: 1", captured_output)
    assert re.search(r"Account name: bank_1_savings", captured_output)
    assert re.search(r"Savings account at bank 1", captured_output)
    assert re.search(r"Currency: CHF", captured_output)
    assert re.search(r"Category: savings", captured_output)
    assert re.search(r"Status: inactive", captured_output)
    assert re.search(r"Account updated successfully", captured_output)
