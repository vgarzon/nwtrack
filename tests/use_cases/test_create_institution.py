"""Tests for institution creator use case."""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

import nwtrack.entrypoints.cli.adapters.institution_presenters
from nwtrack.application.use_cases.create_institution import (
    CreateInstitutionInteractive,
)
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.adapters.institution_presenters import (
    RichInstitutionCreationPresenter,
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
            RichInstitutionCreationPresenter,
            lambda c: RichInstitutionCreationPresenter(console=c.resolve(Console)),
        )
        .register(
            CreateInstitutionInteractive,
            lambda c: CreateInstitutionInteractive(
                uow=lambda: c.resolve(UnitOfWork),
                presenter=c.resolve(RichInstitutionCreationPresenter),
            ),
        )
    )


def test_create_institution_run(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Institution create workflow should succeed with valid input."""
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.institution_presenters,
        "prompt_for_institution_name",
        lambda *args, **kwargs: "Chase",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.institution_presenters,
        "prompt_for_institution_description",
        lambda *args, **kwargs: "Primary bank",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.institution_presenters,
        "prompt_to_confirm_action",
        lambda *args, **kwargs: True,
    )

    service: CreateInstitutionInteractive = configured_container.resolve(
        CreateInstitutionInteractive
    )
    result = service.run()

    assert result.success
    assert result.data == "Chase"
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()
    assert re.search(r"Institution 'Chase' created successfully", captured_output)
    assert re.search(r"Institution name: Chase", captured_output)


def test_create_institution_rejects_duplicate_name(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Create should reject duplicate institution names case-insensitively."""
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.domain.models import Institution

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        uow.institutions.insert(Institution(name="Chase", description="Primary bank"))

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.institution_presenters,
        "prompt_for_institution_name",
        lambda *args, **kwargs: "chase",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.institution_presenters,
        "prompt_for_institution_description",
        lambda *args, **kwargs: "Duplicate bank",
    )

    service: CreateInstitutionInteractive = configured_container.resolve(
        CreateInstitutionInteractive
    )
    result = service.run()

    assert not result.success
    assert result.error_message == "Duplicate institution name"
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()
    assert re.search(r"Institution name 'chase' already exists", captured_output)


def test_create_institution_cancellation(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Create should stop cleanly when the user cancels input."""
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.institution_presenters,
        "prompt_for_institution_name",
        lambda *args, **kwargs: "q",
    )

    service: CreateInstitutionInteractive = configured_container.resolve(
        CreateInstitutionInteractive
    )
    result = service.run()

    assert not result.success
    assert result.error_message == "Cancelled by user"
