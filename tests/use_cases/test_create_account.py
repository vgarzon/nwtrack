"""
Tests for account creator use case
"""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

import nwtrack.entrypoints.cli.adapters.account_presenters
from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.create_account import AccountCreator
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Institution
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.adapters.account_presenters import (
    RichAccountCreationPresenter,
)
from nwtrack.entrypoints.cli.ui.console import ConsoleSettings, build_console


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
            lambda _: build_console(ConsoleSettings(record=True)),
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
    init_db_tables_w_entities(configured_container, sample_entities)

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
        "prompt_for_optional_institution_choice",
        lambda *args, **kwargs: pytest.fail(
            "Institution choice should not be prompted when no institutions exist."
        ),
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
    assert account_id == 5
    assert balance_id > 0

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        created_account = uow.accounts.get_by_id(account_id)
    assert created_account is not None
    assert created_account.institution_id is None

    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()

    assert re.search(r"Account created successfully", captured_output)
    assert re.search(r"Account name: savings_account_3", captured_output)
    assert re.search(r"Account ID: 5", captured_output)
    assert re.search(r"Initial month: 2025-10", captured_output)
    assert re.search(r"Initial balance: 100", captured_output)
    assert re.search(r"Institution: None", captured_output)
    assert re.search(
        r"No institutions available\. Continuing with no institution assigned\.",
        captured_output,
    )


def test_account_creator_run_success_with_selected_institution(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        institution_id = uow.institutions.insert(
            Institution(name="Chase", description="Primary bank")
        )

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_for_account_name",
        lambda *args, **kwargs: "brokerage_account",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_for_account_description",
        lambda *args, **kwargs: "Brokerage at Chase",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_for_category_choice",
        lambda *args, **kwargs: 2,
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
        "prompt_for_optional_institution_choice",
        lambda *args, **kwargs: 2,
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_for_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_for_balance_amount",
        lambda *args, **kwargs: 500,
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.account_presenters,
        "prompt_to_confirm_action",
        lambda *args, **kwargs: True,
    )

    result: OperationResult[tuple[int, int]] = configured_container.resolve(
        AccountCreator
    ).run()

    assert result.success
    assert result.data is not None
    account_id, _ = result.data

    refresh_uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with refresh_uow as uow:
        created_account = uow.accounts.get_by_id(account_id)
    assert created_account is not None
    assert created_account.institution_id == institution_id

    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()

    assert re.search(r"Institutions", captured_output)
    assert re.search(r"None", captured_output)
    assert re.search(r"Institution: Chase", captured_output)
