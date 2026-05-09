"""Tests for institution updater use case."""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

import nwtrack.entrypoints.cli.adapters.institution_presenters
from nwtrack.application.use_cases.update_institution import (
    UpdateInstitutionInteractive,
)
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.adapters.institution_presenters import (
    RichInstitutionUpdatePresenter,
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
            RichInstitutionUpdatePresenter,
            lambda c: RichInstitutionUpdatePresenter(console=c.resolve(Console)),
        )
        .register(
            UpdateInstitutionInteractive,
            lambda c: UpdateInstitutionInteractive(
                uow=lambda: c.resolve(UnitOfWork),
                presenter=c.resolve(RichInstitutionUpdatePresenter),
            ),
        )
    )


def test_update_institution_run(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Institution update workflow should succeed for a valid ID."""
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.domain.models import Institution

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        uow.institutions.insert(Institution(name="Chase", description="Primary bank"))

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.institution_presenters,
        "prompt_for_institution_id",
        lambda *args, **kwargs: 1,
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.institution_presenters,
        "prompt_for_institution_name",
        lambda *args, **kwargs: "Chase Bank",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.institution_presenters,
        "prompt_for_institution_description",
        lambda *args, **kwargs: "Updated description",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.institution_presenters.Confirm,
        "ask",
        lambda *args, **kwargs: True,
    )

    service: UpdateInstitutionInteractive = configured_container.resolve(
        UpdateInstitutionInteractive
    )
    result = service.run()

    assert result.success
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()
    assert re.search(r"Institution updated successfully", captured_output)
    assert re.search(r"Chase Bank", captured_output)
