"""
Tests for balance deleter use case
"""

import re

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import BalanceDeleterPresenter
from nwtrack.application.use_cases.delete_balance import BalanceDeleter
from nwtrack.bootstrap.container import Container
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.console import Console


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""

    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.application.use_cases.delete_balance import (
        BalanceDeleter,
        FetchService,
    )
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.entrypoints.cli.adapters.balance_presenters import (
        RichBalanceDeleterPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings
    from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory
    from nwtrack.infra.config.settings import Settings
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    console_default = ConsoleSettings(record=True)

    return (
        base_container.register(
            SchemaManager,
            lambda c: SchemaManagerImpl(
                engine=c.resolve(SQLiteSessionManager).engine
            ),
        ).register(
            DBAdminService,
            lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
        )
        .register(
            Console,
            lambda _: ConsoleFactory(default_settings=console_default)(),
            lifetime=Lifetime.SINGLETON,
        )
        .register(
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            BalanceDeleterPresenter,
            lambda c: RichBalanceDeleterPresenter(console=c.resolve(Console)),
        )
        .register(
            BalanceDeleter,
            lambda c: BalanceDeleter(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(BalanceDeleterPresenter),
            ),
        )
    )


def test_balance_deleter_run_success(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Test successful balance deletion."""
    import nwtrack.application.use_cases.delete_balance as delete_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    # Mock prompts to simulate user input
    monkeypatch.setattr(
        delete_balance.BalanceDeleter,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceDeleterPresenter,
        "select_account",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceDeleterPresenter,
        "prompt_to_confirm_deletion",
        lambda *args, **kwargs: True,
    )
    result: OperationResult = configured_container.resolve(BalanceDeleter).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    # TODO: check record was deleted from database
    assert result.success
    assert re.search(r"Balance deleted successfully", captured_output)
    assert re.search(r".+1.+bank_1_checking", captured_output)
    assert not re.search(r"deleted successfully.+1.+bank_1_checking", captured_output)


def test_balance_deleter_user_cancellation(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Test user cancels deletion at confirmation."""
    import nwtrack.application.use_cases.delete_balance as delete_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    # Mock prompts to simulate user input
    monkeypatch.setattr(
        delete_balance.BalanceDeleter,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceDeleterPresenter,
        "select_account",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceDeleterPresenter,
        "prompt_to_confirm_deletion",
        lambda *args, **kwargs: False,
    )
    result: OperationResult = configured_container.resolve(BalanceDeleter).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    # TODO: check record was not deleted from database
    assert not result.success
    assert re.search(r"Operation canceled by user", captured_output)


def test_balance_deleter_quit_at_month_selection(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Test user quits at month selection."""
    import nwtrack.application.use_cases.delete_balance as delete_balance

    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        delete_balance.BalanceDeleter,
        "_select_month",
        lambda *args, **kwargs: None,
    )
    result: OperationResult = configured_container.resolve(BalanceDeleter).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert not result.success
    assert re.search(r"Operation canceled by user", captured_output)


def test_balance_deleter_quit_at_account_selection(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Test user quits at account selection."""
    import nwtrack.application.use_cases.delete_balance as delete_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    # Mock prompts to simulate user input
    monkeypatch.setattr(
        delete_balance.BalanceDeleter,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceDeleterPresenter,
        "select_account",
        lambda *args, **kwargs: None,
    )
    result: OperationResult = configured_container.resolve(BalanceDeleter).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert not result.success
    assert re.search(r"Operation canceled by user", captured_output)


def test_balance_deleter_balance_not_found(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Test balance not found for selected account/month."""
    import nwtrack.application.use_cases.delete_balance as delete_balance
    import nwtrack.entrypoints.cli.adapters.balance_presenters as balance_presenters

    init_db_tables_w_entities(configured_container, sample_entities)

    # Mock prompts to simulate user input
    monkeypatch.setattr(
        delete_balance.BalanceDeleter,
        "_select_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        balance_presenters.RichBalanceDeleterPresenter,
        "select_account",
        lambda *args, **kwargs: 999,
    )
    result: OperationResult = configured_container.resolve(BalanceDeleter).run()
    captured_output: str = configured_container.resolve(Console).export_text()

    assert not result.success
    assert re.search(r"No balance found for account 999 on 2025-11", captured_output)
