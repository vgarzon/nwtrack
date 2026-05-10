"""Tests for tag creator use case."""

import re

import pytest
from rich.console import Console
from tests.helpers import init_db_tables_w_entities

import nwtrack.entrypoints.cli.adapters.tag_presenters
from nwtrack.application.use_cases.create_tag import CreateTagInteractive
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.adapters.tag_presenters import RichTagCreationPresenter
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
            RichTagCreationPresenter,
            lambda c: RichTagCreationPresenter(console=c.resolve(Console)),
        )
        .register(
            CreateTagInteractive,
            lambda c: CreateTagInteractive(
                uow=lambda: c.resolve(UnitOfWork),
                presenter=c.resolve(RichTagCreationPresenter),
            ),
        )
    )


def test_create_tag_run(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Tag create workflow should succeed with normalized input."""
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_name",
        lambda *args, **kwargs: "  Liquid   Assets  ",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_description",
        lambda *args, **kwargs: "Quick access",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_to_confirm_action",
        lambda *args, **kwargs: True,
    )

    service: CreateTagInteractive = configured_container.resolve(CreateTagInteractive)
    result = service.run()

    assert result.success
    assert result.data == "liquid assets"
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()
    assert re.search(r"Tag 'liquid assets' created successfully", captured_output)
    assert re.search(r"Tag name: liquid assets", captured_output)


def test_create_tag_rejects_duplicate_name_after_normalization(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Create should reject duplicate tag names after normalization."""
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.domain.models import Tag

    init_db_tables_w_entities(configured_container, sample_entities)
    uow: UnitOfWork = configured_container.resolve(UnitOfWork)
    with uow:
        uow.tags.insert(Tag(name="liquid assets", description="Existing"))

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_name",
        lambda *args, **kwargs: "LIQUID   ASSETS",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_description",
        lambda *args, **kwargs: "Duplicate",
    )

    service: CreateTagInteractive = configured_container.resolve(CreateTagInteractive)
    result = service.run()

    assert not result.success
    assert result.error_message == "Duplicate tag name"
    console: Console = configured_container.resolve(Console)
    captured_output = console.export_text()
    assert re.search(r"Tag name 'liquid assets' already exists", captured_output)


def test_create_tag_rejects_empty_name_after_normalization(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Create should reject a name that becomes empty after normalization."""
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_name",
        lambda *args, **kwargs: "   ",
    )
    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_description",
        lambda *args, **kwargs: "Unused",
    )

    service: CreateTagInteractive = configured_container.resolve(CreateTagInteractive)
    result = service.run()

    assert not result.success
    assert result.error_message == "Tag name cannot be empty after normalization"
    console: Console = configured_container.resolve(Console)
    assert "Tag name cannot be empty after normalization." in console.export_text()


def test_create_tag_cancellation(
    configured_container: Container,
    sample_entities: dict[str, list],
    monkeypatch,
) -> None:
    """Create should stop cleanly when the user cancels input."""
    init_db_tables_w_entities(configured_container, sample_entities)

    monkeypatch.setattr(
        nwtrack.entrypoints.cli.adapters.tag_presenters,
        "prompt_for_tag_name",
        lambda *args, **kwargs: "q",
    )

    service: CreateTagInteractive = configured_container.resolve(CreateTagInteractive)
    result = service.run()

    assert not result.success
    assert result.error_message == "Cancelled by user"
