"""
Tests for list accounts service
"""

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.use_cases.list_accounts import (
    FetchService,
    ListAccounts,
)
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Account, Tag
from nwtrack.infra.config.settings import Settings


class MockAccountListPresenter:
    """Mock presenter for testing that records calls and captures output."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.displayed_accounts: list[Account] = []
        self.active_only_flag: bool = True

    def display_accounts(
        self,
        accounts: list[Account],
        active_only: bool = True,
    ) -> None:
        """Capture display call and store data for assertions."""
        self.calls.append("display_accounts")
        self.displayed_accounts = accounts
        self.active_only_flag = active_only


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""

    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    mock_presenter = MockAccountListPresenter()

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
            FetchService,
            lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
        )
        .register(
            MockAccountListPresenter,
            lambda _: mock_presenter,
        )
        .register(
            ListAccounts,
            lambda c: ListAccounts(
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(MockAccountListPresenter),
            ),
        )
    )


def test_list_accounts_active_only(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    service: ListAccounts = configured_container.resolve(ListAccounts)
    mock_presenter: MockAccountListPresenter = configured_container.resolve(
        MockAccountListPresenter
    )

    result = service.run(active_only=True)

    assert result.success
    assert "display_accounts" in mock_presenter.calls
    assert mock_presenter.active_only_flag is True

    # Verify only active accounts are displayed
    account_names = [acc.name for acc in mock_presenter.displayed_accounts]
    assert "credit_cards_1" in account_names
    assert "mortgage_1" not in account_names  # inactive account


def test_list_all_accounts(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    init_db_tables_w_entities(configured_container, sample_entities)
    service: ListAccounts = configured_container.resolve(ListAccounts)
    mock_presenter: MockAccountListPresenter = configured_container.resolve(
        MockAccountListPresenter
    )

    result = service.run(active_only=False)

    assert result.success
    assert "display_accounts" in mock_presenter.calls
    assert mock_presenter.active_only_flag is False

    # Verify all accounts are displayed
    account_names = [acc.name for acc in mock_presenter.displayed_accounts]
    assert "credit_cards_1" in account_names
    assert "mortgage_1" in account_names  # inactive account included


def test_list_accounts_exposes_assigned_tags(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Account list reads should include tags for presenter rendering."""
    init_db_tables_w_entities(configured_container, sample_entities)
    service: ListAccounts = configured_container.resolve(ListAccounts)
    mock_presenter: MockAccountListPresenter = configured_container.resolve(
        MockAccountListPresenter
    )

    from nwtrack.application.ports.uow import UnitOfWork

    uow_manager: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow_manager as uow:
        tag_id = uow.tags.insert(Tag(name="liquid", description="Quick access"))
        uow.tags.replace_for_account(1, [tag_id])

    result = service.run(active_only=False)

    assert result.success
    listed_account = next(
        account for account in mock_presenter.displayed_accounts if account.id == 1
    )
    assert [tag.name for tag in listed_account.tags] == ["liquid"]
