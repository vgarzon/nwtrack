"""Tests for the balance creation use case."""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.ports.presentation import BalanceCreationPresenter
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.create_balance import BalanceCreator
from nwtrack.bootstrap.container import Container, Lifetime
from nwtrack.domain.models import Status
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.adapters.balance_presenters import (
    RichBalanceCreationPresenter,
)
from nwtrack.entrypoints.cli.ui.console import ConsoleSettings, build_console
from nwtrack.infra.config.settings import Settings


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Configure container for balance creation tests."""
    from nwtrack.application.ports.schema import SchemaManager
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
            InitDataService,
            lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
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
            BalanceCreationPresenter,
            lambda c: RichBalanceCreationPresenter(console=c.resolve(Console)),
        )
        .register(
            BalanceCreator,
            lambda c: BalanceCreator(
                uow=lambda: c.resolve(UnitOfWork),
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(BalanceCreationPresenter),
            ),
        )
    )


def test_balance_creator_creates_missing_balance(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """A missing balance row should be created successfully."""
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        RichBalanceCreationPresenter,
        "select_account",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        RichBalanceCreationPresenter,
        "collect_month",
        lambda *args, **kwargs: Month(2025, 12),
    )
    monkeypatch.setattr(
        RichBalanceCreationPresenter,
        "collect_amount",
        lambda *args, **kwargs: 350,
    )
    monkeypatch.setattr(
        RichBalanceCreationPresenter,
        "show_preview_and_confirm",
        lambda *args, **kwargs: True,
    )

    result = configured_container.resolve(BalanceCreator).run()

    assert result.success
    assert result.data is not None

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        created_balance = uow.balances.get_by_account_id(Month(2025, 12), 1)
    assert created_balance.amount == 350

    output = configured_container.resolve(Console).export_text()
    assert re.search(r"Active Accounts", output)
    assert re.search(r"Balance created successfully", output)
    assert re.search(r"Created balance:", output)
    assert re.search(r"Month: 2025-12", output)


def test_balance_creator_exits_when_no_active_accounts(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """The workflow should exit cleanly when no active accounts are eligible."""
    init_db_tables_w_entities(configured_container, sample_entities)

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        for account in uow.accounts.get_all():
            account.status = Status.INACTIVE
            uow.accounts.update(account)

    result = configured_container.resolve(BalanceCreator).run()

    assert not result.success
    assert result.error_message == "No active accounts."

    output = configured_container.resolve(Console).export_text()
    assert re.search(r"No active accounts available for balance creation", output)


def test_balance_creator_rejects_duplicate_and_points_to_update(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Duplicate create should be rejected without overwriting the existing row."""
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        RichBalanceCreationPresenter,
        "select_account",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        RichBalanceCreationPresenter,
        "collect_month",
        lambda *args, **kwargs: Month(2025, 11),
    )
    monkeypatch.setattr(
        RichBalanceCreationPresenter,
        "collect_amount",
        lambda *args, **kwargs: pytest.fail(
            "Amount entry should not be reached for a duplicate account/month."
        ),
    )

    result = configured_container.resolve(BalanceCreator).run()

    assert not result.success
    assert result.error_message == "Duplicate balance"

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        existing_balance = uow.balances.get_by_account_id(Month(2025, 11), 1)
    assert existing_balance.amount == 200

    output = configured_container.resolve(Console).export_text()
    assert re.search(r"Balance already exists for account 1 in 2025-11", output)
    assert re.search(r"balances update", output)


def test_balance_creator_cancels_before_confirmation_without_insert(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Cancellation before confirmation should leave the database unchanged."""
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        RichBalanceCreationPresenter,
        "select_account",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        RichBalanceCreationPresenter,
        "collect_month",
        lambda *args, **kwargs: Month(2025, 12),
    )
    monkeypatch.setattr(
        RichBalanceCreationPresenter,
        "collect_amount",
        lambda *args, **kwargs: None,
    )

    result = configured_container.resolve(BalanceCreator).run()

    assert not result.success
    assert result.error_message == "Cancelled by user"

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        existing_balances = uow.balances.get_all_by_account_id(1)
    assert all(str(balance.month) != "2025-12" for balance in existing_balances)

    output = configured_container.resolve(Console).export_text()
    assert re.search(r"Balance creation cancelled", output)
