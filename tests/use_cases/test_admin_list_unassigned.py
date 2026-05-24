"""Tests for ListUnassignedAccounts use case."""

from typing import cast

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.admin_list_unassigned import ListUnassignedAccounts
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Account, Institution
from nwtrack.infra.config.settings import Settings


class MockAdminListUnassignedPresenter:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.displayed_accounts: list[Account] = []

    def display_unassigned(self, accounts: list[Account]) -> None:
        self.calls.append("display_unassigned")
        self.displayed_accounts = accounts

    def show_empty_state(self) -> None:
        self.calls.append("show_empty_state")


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    mock_presenter = MockAdminListUnassignedPresenter()
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
            MockAdminListUnassignedPresenter,
            lambda _: mock_presenter,
        )
        .register(
            ListUnassignedAccounts,
            lambda c: ListUnassignedAccounts(
                fetcher=c.resolve(FetchService),
                presenter=c.resolve(MockAdminListUnassignedPresenter),
            ),
        )
    )


def test_list_unassigned_shows_table_when_accounts_have_no_institution(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """All test accounts have no institution — display_unassigned should be called."""
    init_db_tables_w_entities(configured_container, sample_entities)
    uc: ListUnassignedAccounts = configured_container.resolve(ListUnassignedAccounts)
    presenter: MockAdminListUnassignedPresenter = configured_container.resolve(
        MockAdminListUnassignedPresenter
    )

    result = uc.run()

    assert result.success
    assert "display_unassigned" in presenter.calls
    assert "show_empty_state" not in presenter.calls
    account_names = [a.name for a in presenter.displayed_accounts]
    assert "bank_1_checking" in account_names
    assert "credit_cards_1" in account_names


def test_list_unassigned_shows_empty_state_when_all_assigned(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """After assigning institutions to all accounts, show_empty_state is called."""
    init_db_tables_w_entities(configured_container, sample_entities)

    uow: UnitOfWork
    inst_id: int
    with configured_container.resolve(UnitOfWork) as uow:
        inst_id = uow.institutions.insert(Institution(name="Bank A", description=""))
        acct: Account
        for acct in uow.accounts.get_all():
            updated = Account(
                name=acct.name,
                description=acct.description,
                category_name=acct.category_name,
                currency_code=acct.currency_code,
                institution_id=inst_id,
                status=acct.status,
            )
            updated.id = acct.id
            uow.accounts.update(updated)

    uc: ListUnassignedAccounts = configured_container.resolve(ListUnassignedAccounts)
    presenter: MockAdminListUnassignedPresenter = configured_container.resolve(
        MockAdminListUnassignedPresenter
    )

    result = uc.run()

    assert result.success
    assert "show_empty_state" in presenter.calls
    assert "display_unassigned" not in presenter.calls


def test_list_unassigned_shows_only_accounts_without_institution(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Only accounts with institution_id=NULL should appear in the table."""
    init_db_tables_w_entities(configured_container, sample_entities)

    uow: UnitOfWork
    inst_id: int
    first_account: Account
    assigned_name: str
    with configured_container.resolve(UnitOfWork) as uow:
        inst_id = uow.institutions.insert(Institution(name="Bank B", description=""))
        first_account = uow.accounts.get_all()[0]
        updated = Account(
            name=first_account.name,
            description=first_account.description,
            category_name=first_account.category_name,
            currency_code=first_account.currency_code,
            institution_id=inst_id,
            status=first_account.status,
        )
        updated.id = first_account.id
        uow.accounts.update(updated)
        assigned_name = first_account.name

    uc: ListUnassignedAccounts = configured_container.resolve(ListUnassignedAccounts)
    presenter: MockAdminListUnassignedPresenter = configured_container.resolve(
        MockAdminListUnassignedPresenter
    )

    result = uc.run()

    assert result.success
    assert "display_unassigned" in presenter.calls
    displayed_names = [a.name for a in presenter.displayed_accounts]
    assert assigned_name not in displayed_names
    assert len(presenter.displayed_accounts) == len(sample_entities["accounts"]) - 1


def test_get_without_institution_repo_query_ordered_by_name(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """get_without_institution results should be sorted by account name."""
    init_db_tables_w_entities(configured_container, sample_entities)

    uow: UnitOfWork
    with configured_container.resolve(UnitOfWork) as uow:
        accounts: list[Account] = cast(
            list[Account], uow.accounts.get_without_institution()
        )

    names: list[str] = [a.name for a in accounts]
    assert names == sorted(names)
