"""
Test suite for the balance updater use case
"""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.update_balances import BalanceUpdater
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.adapters.balance_presenters import (
    RichBalanceUpdatePresenter,
)


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Configure container."""
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.data_loader import InitDataService
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.infra.config.settings import Settings
    from nwtrack.infra.sqlite.sqlalchemy_manager import SQLAlchemySessionManager

    return (
        base_container.register(
            DBAdminService,
            lambda c: DBAdminService(
                c.resolve(Settings), c.resolve(SQLAlchemySessionManager)
            ),
        )
        .register(
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
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
            RichBalanceUpdatePresenter,
            lambda c: RichBalanceUpdatePresenter(console=c.resolve(Console)),
        )
        .register(
            BalanceUpdater,
            lambda c: BalanceUpdater(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(RichBalanceUpdatePresenter),
            ),
        )
    )


def test_update_balances_run(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
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
            300,  # New balance for account 1
            500,  # New balance for account 3
        ]
    )

    def mock_prompt(*args, **kwargs):
        return next(input_prompt)

    def mock_int_prompt(*args, **kwargs):
        return next(input_int_prompt)

    init_db_tables_w_entities(configured_container, sample_entities)

    # Patch the prompt classes
    from rich.prompt import IntPrompt, Prompt

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

    from nwtrack.application.dto import OperationResult

    result: OperationResult[None] = configured_container.resolve(BalanceUpdater).run()

    assert result.success

    # Check console output
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()

    assert re.search(r"Balances 2025-11", captured_output)
    assert re.search(r"Account bank_1_checking.+2025-11.+200", captured_output)
    assert re.search(r"800.+500.+300", captured_output)

    # TODO: Test other interactions
