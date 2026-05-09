"""Tests for listing institutions."""

import pytest
from tests.helpers import init_db_tables_w_entities

from nwtrack.application.dto import InstitutionListItem
from nwtrack.application.use_cases.list_institutions import ListInstitutions
from nwtrack.bootstrap.container import Container
from nwtrack.domain.models import Account, Institution, Status
from nwtrack.infra.config.settings import Settings


class MockInstitutionListPresenter:
    """Mock presenter for testing institution list display."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.displayed_institutions: list[InstitutionListItem] = []

    def display_institutions(self, institutions: list[InstitutionListItem]) -> None:
        self.calls.append("display_institutions")
        self.displayed_institutions = institutions


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register services in the container."""
    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    mock_presenter = MockInstitutionListPresenter()

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
            MockInstitutionListPresenter,
            lambda _: mock_presenter,
        )
        .register(
            ListInstitutions,
            lambda c: ListInstitutions(
                uow=lambda: c.resolve(UnitOfWork),
                presenter=c.resolve(MockInstitutionListPresenter),
            ),
        )
    )


def test_list_institutions_shows_usage_counts(
    configured_container: Container,
    sample_entities: dict[str, list],
) -> None:
    """Institution list should include linked-account counts."""
    from nwtrack.application.ports.uow import UnitOfWork

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        institution_id = uow.institutions.insert(
            Institution(name="Chase", description="Primary bank")
        )
        uow.accounts.insert(
            Account(
                name="chase_checking",
                description="Checking",
                category_name="checking",
                institution_id=institution_id,
                currency_code="USD",
                status=Status.ACTIVE,
            )
        )

    service: ListInstitutions = configured_container.resolve(ListInstitutions)
    mock_presenter: MockInstitutionListPresenter = configured_container.resolve(
        MockInstitutionListPresenter
    )
    result = service.run()

    assert result.success
    assert "display_institutions" in mock_presenter.calls
    assert mock_presenter.displayed_institutions[0].institution.name == "Chase"
    assert mock_presenter.displayed_institutions[0].account_count == 1
