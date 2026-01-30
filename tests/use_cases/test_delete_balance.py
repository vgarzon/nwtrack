"""
Tests for balance deleter use case
"""

import re

import pytest
from tests.helpers import init_db_tables_w_entities

import nwtrack.application.use_cases.delete_balance
from nwtrack.application.use_cases.delete_balance import BalanceDeleter
from nwtrack.bootstrap.container import Container


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.use_cases.delete_balance import (
        BalanceDeleter,
        ConsoleFactory,
        FetchService,
    )
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings
    from nwtrack.infra.config.settings import Settings

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
            BalanceDeleter,
            lambda c: BalanceDeleter(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                console_factory=c.resolve(ConsoleFactory),
            ),
        )
    )


def test_balance_deleter_run_success(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Test successful balance deletion."""
    init_db_tables_w_entities(configured_container, sample_entities)

    # Mock prompts to simulate user input
    monkeypatch.setattr(
        nwtrack.application.use_cases.delete_balance,
        "prompt_for_month_choice",
        lambda *args, **kwargs: "1",  # Select first month
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.delete_balance,
        "prompt_for_account_id",
        lambda *args, **kwargs: 1,  # Select account ID 1
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.delete_balance,
        "prompt_to_confirm_action",
        lambda *args, **kwargs: True,  # Confirm deletion
    )

    service: BalanceDeleter = configured_container.resolve(BalanceDeleter)
    service.run()
    captured_output = service._console.export_text()

    assert re.search(r"Balance deleted successfully", captured_output)


def test_balance_deleter_user_cancellation(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Test user cancels deletion at confirmation."""
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        nwtrack.application.use_cases.delete_balance,
        "prompt_for_month_choice",
        lambda *args, **kwargs: "1",
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.delete_balance,
        "prompt_for_account_id",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.delete_balance,
        "prompt_to_confirm_action",
        lambda *args, **kwargs: False,  # Cancel deletion
    )

    service: BalanceDeleter = configured_container.resolve(BalanceDeleter)
    service.run()
    captured_output = service._console.export_text()

    assert re.search(r"Deletion cancelled", captured_output)


def test_balance_deleter_quit_at_month_selection(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Test user quits at month selection."""
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        nwtrack.application.use_cases.delete_balance,
        "prompt_for_month_choice",
        lambda *args, **kwargs: "q",  # Quit
    )

    service: BalanceDeleter = configured_container.resolve(BalanceDeleter)
    service.run()
    captured_output = service._console.export_text()

    assert re.search(r"No month selected", captured_output)


def test_balance_deleter_quit_at_account_selection(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Test user quits at account selection."""
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        nwtrack.application.use_cases.delete_balance,
        "prompt_for_month_choice",
        lambda *args, **kwargs: "1",
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.delete_balance,
        "prompt_for_account_id",
        lambda *args, **kwargs: None,  # User quit
    )

    service: BalanceDeleter = configured_container.resolve(BalanceDeleter)
    service.run()
    captured_output = service._console.export_text()

    assert re.search(r"Operation cancelled", captured_output)


def test_balance_deleter_balance_not_found(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Test balance not found for selected account/month."""
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        nwtrack.application.use_cases.delete_balance,
        "prompt_for_month_choice",
        lambda *args, **kwargs: "1",
    )
    monkeypatch.setattr(
        nwtrack.application.use_cases.delete_balance,
        "prompt_for_account_id",
        lambda *args, **kwargs: 999,  # Non-existent account
    )

    service: BalanceDeleter = configured_container.resolve(BalanceDeleter)
    service.run()
    captured_output = service._console.export_text()

    assert re.search(r"No balance found", captured_output)
