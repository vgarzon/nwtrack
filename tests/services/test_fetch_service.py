"""Tests for narrow fetch-service institution support."""

import pytest

from nwtrack.application.ports.schema import SchemaManager
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.application.services.fetch import FetchService
from nwtrack.bootstrap.container import Container
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl
from nwtrack.domain.models import Institution
from tests.helpers import init_db_tables_w_entities


@pytest.fixture
def configured_container(base_container: Container) -> Container:
    """Register the services needed to initialize test data."""
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
    )


def test_fetch_service_lists_institutions_for_account_workflows(
    configured_container: Container, sample_entities
) -> None:
    """Account workflows should only need institution listing from FetchService."""
    init_db_tables_w_entities(configured_container, sample_entities)
    fetcher = FetchService(uow=lambda: configured_container.resolve(UnitOfWork))

    with configured_container.resolve(UnitOfWork) as uow:
        uow.institutions.insert(Institution(name="Chase", description="Primary bank"))
        uow.institutions.insert(Institution(name="Fidelity", description="Brokerage"))

    institutions = fetcher.get_all_institutions()

    assert [institution.name for institution in institutions] == ["Chase", "Fidelity"]
